package dev.celestial.memory;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import dev.celestial.Celestial;
import dev.celestial.data.CelestialData;
import dev.celestial.network.MemoryOverlayPayload;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.portal.TeleportTransition;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * «Отблески» (docs/LORE.md §5c): странник касается места, которое помнит, и проживает воспоминание, а потом возвращается туда же,
 * откуда ушёл, — в ту же точку и с тем же взглядом.
 *
 * Как устроено: у каждого игрока свой «слот» в карманном измерении `celestial:memory` (x = слот × 512). При входе туда ставится шаблон
 * сцены, появляются актёры ({@link MemoryActor}), игрок переносится и переводится в режим «Приключение» (ломать и строить нельзя),
 * становится неуязвим. Сцена идёт по шагам ({@link MemoryScenes}); шаги-«триггеры» ждут странника (подошёл, посмотрел), а не секундомер.
 * Уйти за границу памяти нельзя: она «осыпается» и мягко разворачивает. Точка возврата хранится во вложении игрока —
 * если он вышел из игры посреди воспоминания, при входе его вернёт обратно.
 *
 * В одиночной игре мир на время воспоминания фактически замирает: игрок далеко, чанки вокруг точки возврата не обновляются.
 */
public final class Memories {
	public static final ResourceKey<Level> MEMORY = ResourceKey.create(Registries.DIMENSION, Celestial.id("memory"));
	public static final AttachmentType<MemoryReturn> RETURN = AttachmentRegistry.<MemoryReturn>builder()
		.persistent(MemoryReturn.CODEC)
		.buildAndRegister(Celestial.id("memory_return"));

	private static final int SLOT_SPACING = 512;
	private static final int STAGE_Y = 64;
	private static final int COMBAT_COOLDOWN = 100;   // 5 с после урона войти нельзя
	private static final int TRIGGER_TIMEOUT = 1200;  // страница не застрянет навсегда: через минуту триггер срабатывает сам
	private static final int SKIP_SNEAK_TICKS = 40;   // пропуск уже виденного: удерживать «красться» 2 с
	private static final Map<UUID, Session> SESSIONS = new HashMap<>();

	private Memories() {}

	public static void init() {
		PayloadTypeRegistry.clientboundPlay().register(MemoryOverlayPayload.TYPE, MemoryOverlayPayload.CODEC);
		ServerTickEvents.END_SERVER_TICK.register(Memories::tick);
		// в воспоминании странник неуязвим: это память, а не бой
		net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) ->
			!(entity instanceof ServerPlayer p && (inMemory(p) || p.level().dimension() == MEMORY)));
		PayloadTypeRegistry.serverboundPlay().register(dev.celestial.network.ReplayMemoryPayload.TYPE, dev.celestial.network.ReplayMemoryPayload.CODEC);
		// «Пережить снова» из Кодекса — только уже пережитое
		ServerPlayNetworking.registerGlobalReceiver(dev.celestial.network.ReplayMemoryPayload.TYPE, (payload, ctx) -> {
			ServerPlayer p = ctx.player();
			if (CelestialData.get(p).knows("memory:" + payload.scene())) {
				tryEnter(p, payload.scene(), p.blockPosition());
			}
		});
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> server.execute(() -> rescue(handler.player)));
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
			Session s = SESSIONS.remove(handler.player.getUUID());
			if (s != null) {
				s.cleanup();
			}
		});
	}

	public static boolean inMemory(ServerPlayer player) {
		return SESSIONS.containsKey(player.getUUID());
	}

	/** Попытка войти в воспоминание у якоря. Отказ — с объяснением в строке над панелью. */
	public static boolean tryEnter(ServerPlayer player, String sceneId, BlockPos anchor) {
		var scene = MemoryScenes.get(sceneId);
		if (scene.isEmpty()) {
			player.sendOverlayMessage(Component.translatable("memory.celestial.blank"));
			return false;
		}
		String why = null;
		if (inMemory(player) || player.level().dimension() == MEMORY) {
			why = "memory.celestial.deny.already";
		} else if (player.getLastHurtByMobTimestamp() > 0 && player.tickCount - player.getLastHurtByMobTimestamp() < COMBAT_COOLDOWN
			|| player.hurtTime > 0) {
			why = "memory.celestial.deny.combat";
		} else if (player.isPassenger() || player.isFallFlying() || !player.onGround() || player.isInLava()) {
			why = "memory.celestial.deny.unsteady";
		}
		if (why != null) {
			player.sendOverlayMessage(Component.translatable(why).withStyle(ChatFormatting.GRAY));
			return false;
		}
		ServerLevel memory = player.level().getServer().getLevel(MEMORY);
		if (memory == null) {
			Celestial.LOGGER.error("Нет измерения воспоминаний {}", MEMORY.identifier());
			return false;
		}
		enter(player, memory, scene.get(), anchor);
		return true;
	}

	private static int slotFor(ServerPlayer player) {
		// у каждого присутствующего игрока свой слот: берём первый свободный
		java.util.Set<Integer> used = new java.util.HashSet<>();
		for (Session s : SESSIONS.values()) {
			used.add(s.slot);
		}
		int slot = 0;
		while (used.contains(slot)) {
			slot++;
		}
		return slot;
	}

	private static void enter(ServerPlayer player, ServerLevel memory, MemoryScenes.Scene scene, BlockPos anchor) {
		int slot = slotFor(player);
		BlockPos origin = new BlockPos(slot * SLOT_SPACING, STAGE_Y, 0);
		memory.getChunkSource().getChunk(origin.getX() >> 4, origin.getZ() >> 4, true);
		for (Entity e : memory.getEntitiesOfClass(Entity.class, new AABB(origin).inflate(96), e -> !(e instanceof ServerPlayer))) {
			e.discard();  // остатки прошлого входа
		}
		var template = memory.getServer().getStructureTemplateManager().get(Identifier.parse(scene.stage()));
		if (template.isEmpty()) {
			Celestial.LOGGER.error("Нет шаблона сцены {}", scene.stage());
			player.sendOverlayMessage(Component.translatable("memory.celestial.blank"));
			return;
		}
		template.get().placeInWorld(memory, origin, origin, new StructurePlaceSettings(), memory.getRandom(), 2);
		player.setAttached(RETURN, new MemoryReturn(player.level().dimension().identifier().toString(), player.getX(), player.getY(), player.getZ(),
			player.getYRot(), player.getXRot(), player.gameMode.getGameModeForPlayer().getName(), anchor, scene.id(),
			!CelestialData.get(player).knows("memory:" + scene.id())));
		Session session = new Session(player, scene, memory, origin, slot);
		SESSIONS.put(player.getUUID(), session);
		player.level().playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.0F, 0.6F);
		player.teleport(new TeleportTransition(memory, at(origin, scene.spawn()), Vec3.ZERO, scene.spawnYaw(), 0.0F, TeleportTransition.DO_NOTHING));
		if (player.gameMode.getGameModeForPlayer() != GameType.CREATIVE && player.gameMode.getGameModeForPlayer() != GameType.SPECTATOR) {
			player.setGameMode(GameType.ADVENTURE);
		}
		for (MemoryScenes.Actor a : scene.actors()) {
			session.spawn(a);
		}
		ServerPlayNetworking.send(player, new MemoryOverlayPayload(true, 0.0F));
	}

	static Vec3 at(BlockPos origin, Vec3 rel) {
		return new Vec3(origin.getX() + rel.x, origin.getY() + rel.y, origin.getZ() + rel.z);
	}

	/** Игрок вошёл в мир и оказался в измерении памяти без сессии (вышел посреди воспоминания) — вернуть. */
	private static void rescue(ServerPlayer player) {
		if (player.level().dimension() == MEMORY && !inMemory(player)) {
			returnPlayer(player, false);
		}
	}

	private static void returnPlayer(ServerPlayer player, boolean completed) {
		MemoryReturn back = player.getAttached(RETURN);
		player.removeAttached(RETURN);
		ServerPlayNetworking.send(player, new MemoryOverlayPayload(false, 0.0F));
		MinecraftServer server = player.level().getServer();
		ServerLevel target = server.overworld();
		Vec3 pos = Vec3.atBottomCenterOf(target.getRespawnData().pos());
		float yaw = player.getYRot();
		float pitch = player.getXRot();
		if (back != null) {
			ServerLevel l = server.getLevel(ResourceKey.create(Registries.DIMENSION, Identifier.parse(back.dimension())));
			if (l != null) {
				target = l;
				pos = new Vec3(back.x(), back.y(), back.z());
				yaw = back.yaw();
				pitch = back.pitch();
			}
			GameType mode = GameType.byName(back.gameMode(), GameType.SURVIVAL);
			if (player.gameMode.getGameModeForPlayer() != mode) {
				player.setGameMode(mode);
			}
		}
		player.teleport(new TeleportTransition(target, pos, Vec3.ZERO, yaw, pitch, TeleportTransition.DO_NOTHING));
		if (completed && back != null) {
			consequences(player, target, back);
		}
	}

	/** Последствия прожитого воспоминания в настоящем: лист Летописи, мысль, а иногда — перемена у якоря. */
	private static void consequences(ServerPlayer player, ServerLevel level, MemoryReturn back) {
		var scene = MemoryScenes.get(back.scene());
		if (scene.isEmpty()) {
			return;
		}
		MemoryScenes.Scene s = scene.get();
		CelestialData.update(player, d -> d.withCodex("memory:" + s.id()));
		if (!s.sheet().isEmpty()) {
			dev.celestial.lore.Lore.unlock(player, s.sheet());
		}
		if (!s.thought().isEmpty()) {
			dev.celestial.boss.BossIntro.title(player, Component.empty(),
				Component.translatable(s.thought()).withStyle(ChatFormatting.ITALIC, ChatFormatting.GOLD), 80);
		}
		level.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.0F, 0.8F);
		if (back.first() && s.onComplete().equals("part_thorns")) {  // перемена у якоря — только в первый раз, не при повторе из Кодекса
			// терновник вокруг Древа Познания расступается: тропа к Восточным вратам открыта
			BlockPos a = back.anchor();
			for (BlockPos p : BlockPos.betweenClosed(a.offset(-7, -2, -7), a.offset(7, 3, 7))) {
				if (level.getBlockState(p).is(Blocks.SWEET_BERRY_BUSH)) {
					level.destroyBlock(p, false);
					level.sendParticles(ParticleTypes.END_ROD, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 3, 0.3, 0.3, 0.3, 0.02);
				}
			}
		}
	}

	private static void tick(MinecraftServer server) {
		Iterator<Session> it = SESSIONS.values().iterator();
		List<Session> done = new ArrayList<>();
		while (it.hasNext()) {
			Session s = it.next();
			if (s.player.isRemoved() || s.player.level() != s.level) {
				s.cleanup();
				it.remove();
				continue;
			}
			if (s.tick()) {
				done.add(s);
				it.remove();
			}
		}
		for (Session s : done) {
			s.cleanup();
			returnPlayer(s.player, true);
		}
	}

	// ---------------------------------------------------------------- сессия
	private static final class Session {
		final ServerPlayer player;
		final MemoryScenes.Scene scene;
		final ServerLevel level;
		final BlockPos origin;
		final int slot;
		final Map<String, MemoryActor> actors = new HashMap<>();
		final Map<String, Display.ItemDisplay> held = new HashMap<>();
		final Map<String, Vec3> moveTargets = new HashMap<>();
		final Map<String, Double> moveSpeeds = new HashMap<>();
		int step;
		int stepTicks;
		int sneakTicks;
		final boolean seen;

		Session(ServerPlayer player, MemoryScenes.Scene scene, ServerLevel level, BlockPos origin, int slot) {
			this.player = player;
			this.scene = scene;
			this.level = level;
			this.origin = origin;
			this.slot = slot;
			this.seen = CelestialData.get(player).knows("memory:" + scene.id());
		}

		void spawn(MemoryScenes.Actor a) {
			EntityType<MemoryActor> type = a.type().equals("serpent") ? dev.celestial.registry.ModEntities.MEMORY_SERPENT
				: dev.celestial.registry.ModEntities.MEMORY_HUMAN;
			MemoryActor actor = type.create(level, EntitySpawnReason.TRIGGERED);
			if (actor == null) {
				return;
			}
			Vec3 p = at(origin, a.pos());
			actor.snapTo(p.x, p.y, p.z, a.yaw(), 0.0F);
			actor.setYHeadRot(a.yaw());
			actor.setYBodyRot(a.yaw());
			actor.setSkin(a.skin());
			actor.setScenePose(a.pose());
			level.addFreshEntity(actor);
			actors.put(a.id(), actor);
		}

		void cleanup() {
			actors.values().forEach(Entity::discard);
			held.values().forEach(Entity::discard);
			extra.forEach(Entity::discard);
			actors.clear();
			held.clear();
			extra.clear();
		}

		/** true — сцена окончена. */
		boolean tick() {
			// пропуск уже пережитого: удерживать «красться»
			if (seen && player.isShiftKeyDown()) {
				if (++sneakTicks >= SKIP_SNEAK_TICKS) {
					return true;
				}
			} else {
				sneakTicks = 0;
			}
			boundary();
			moveActors();
			syncHeld();
			// выполняем шаги, пока очередной не попросит подождать
			for (int guard = 0; guard < 32 && step < scene.steps().size(); guard++) {
				JsonObject st = scene.steps().get(step);
				if (!run(st)) {
					stepTicks++;
					return false;
				}
				step++;
				stepTicks = 0;
			}
			return step >= scene.steps().size();
		}

		/** Граница памяти: дальше радиуса память «осыпается» и разворачивает странника к центру. Ниже сцены — обратно на точку появления. */
		void boundary() {
			Vec3 c = at(origin, scene.center());
			double dx = player.getX() - c.x;
			double dz = player.getZ() - c.z;
			double d = Math.sqrt(dx * dx + dz * dz);
			if (player.getY() < origin.getY() - 8) {
				Vec3 sp = at(origin, scene.spawn());
				player.teleport(new TeleportTransition(level, sp, Vec3.ZERO, scene.spawnYaw(), 0.0F, TeleportTransition.DO_NOTHING));
				return;
			}
			if (d > scene.radius()) {
				player.push(-dx / d * 0.35, 0.05, -dz / d * 0.35);
				player.syncVelocity = true;
				level.sendParticles(ParticleTypes.END_ROD, player.getX() + dx / d, player.getY() + 1, player.getZ() + dz / d, 12, 0.6, 0.8, 0.6, 0.02);
				if (player.tickCount % 20 == 0) {
					player.sendOverlayMessage(Component.translatable("memory.celestial.edge").withStyle(ChatFormatting.ITALIC, ChatFormatting.GRAY));
				}
			}
		}

		void moveActors() {
			for (var e : moveTargets.entrySet()) {
				MemoryActor a = actors.get(e.getKey());
				if (a == null) {
					continue;
				}
				Vec3 to = e.getValue();
				Vec3 from = a.position();
				Vec3 delta = to.subtract(from);
				double len = delta.length();
				double speed = moveSpeeds.getOrDefault(e.getKey(), 0.08);
				if (len < 0.05) {
					continue;
				}
				Vec3 next = len <= speed ? to : from.add(delta.scale(speed / len));
				float yaw = (float) (Mth.atan2(delta.z, delta.x) * Mth.RAD_TO_DEG) - 90.0F;
				a.setPos(next.x, next.y, next.z);
				a.setYRot(yaw);
				a.setYBodyRot(yaw);
				a.setYHeadRot(yaw);
			}
		}

		void syncHeld() {
			for (var e : held.entrySet()) {
				MemoryActor a = actors.get(e.getKey());
				if (a == null) {
					continue;
				}
				float yaw = a.getYRot() * Mth.DEG_TO_RAD;
				double fx = -Mth.sin(yaw), fz = Mth.cos(yaw);
				double rx = -fz, rz = fx;  // правая рука
				double up = a.scenePose() == MemoryActor.EAT ? 1.45 : 1.05;
				double fwd = a.scenePose() == MemoryActor.OFFER ? 0.55 : 0.3;
				e.getValue().setPos(a.getX() + fx * fwd + rx * 0.33, a.getY() + up, a.getZ() + fz * fwd + rz * 0.33);
			}
		}

		Vec3 point(JsonElement e) {
			return at(origin, MemoryScenes.vec(e));
		}

		Vec3 targetOf(JsonElement e) {
			if (e.isJsonPrimitive()) {
				String id = e.getAsString();
				if (id.equals("player")) {
					return player.getEyePosition();
				}
				MemoryActor a = actors.get(id);
				return a != null ? a.getEyePosition() : player.getEyePosition();
			}
			return point(e);
		}

		/** Выполнить шаг. true — шаг закончен, можно дальше. */
		boolean run(JsonObject st) {
			String t = st.get("t").getAsString();
			int timeout = st.has("timeout") ? st.get("timeout").getAsInt() : TRIGGER_TIMEOUT;
			switch (t) {
				case "wait" -> {
					return stepTicks >= st.get("ticks").getAsInt();
				}
				case "near" -> {
					Vec3 p = point(st.get("pos"));
					double r = st.get("r").getAsDouble();
					return player.position().distanceToSqr(p) <= r * r || stepTicks >= timeout;
				}
				case "look" -> {
					MemoryActor a = actors.get(st.get("actor").getAsString());
					if (a == null) {
						return true;
					}
					Vec3 to = a.position().add(0, a.getBbHeight() * 0.6, 0).subtract(player.getEyePosition());
					double r = st.has("r") ? st.get("r").getAsDouble() : 16.0;
					double cos = to.normalize().dot(player.getViewVector(1.0F));
					return (to.length() <= r && cos > 0.94) || stepTicks >= timeout;  // ~20° от центра взгляда
				}
				case "move" -> {
					String id = st.get("actor").getAsString();
					Vec3 to = point(st.get("to"));
					if (stepTicks == 0) {
						moveTargets.put(id, to);
						moveSpeeds.put(id, st.has("speed") ? st.get("speed").getAsDouble() : 0.08);
					}
					MemoryActor a = actors.get(id);
					boolean wait = !st.has("wait") || st.get("wait").getAsBoolean();
					return !wait || a == null || a.position().distanceToSqr(to) < 0.01 || stepTicks > 600;
				}
				case "face" -> {
					MemoryActor a = actors.get(st.get("actor").getAsString());
					if (a != null) {
						moveTargets.remove(st.get("actor").getAsString());
						Vec3 d = targetOf(st.get("to")).subtract(a.position());
						float yaw = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90.0F;
						a.setYRot(yaw);
						a.setYBodyRot(yaw);
						a.setYHeadRot(yaw);
					}
					return true;
				}
				case "pose" -> {
					MemoryActor a = actors.get(st.get("actor").getAsString());
					if (a != null) {
						a.setScenePose(st.get("pose").getAsInt());
					}
					return true;
				}
				case "hold" -> {
					String id = st.get("actor").getAsString();
					Display.ItemDisplay old = held.remove(id);
					if (old != null) {
						old.discard();
					}
					if (st.has("item") && !st.get("item").isJsonNull()) {
						var item = BuiltInRegistries.ITEM.getValue(Identifier.parse(st.get("item").getAsString()));
						Display.ItemDisplay d = EntityTypes.ITEM_DISPLAY.create(level, EntitySpawnReason.TRIGGERED);
						if (d != null) {
							d.setItemStack(new ItemStack(item));
							d.setTransformation(new com.mojang.math.Transformation(null, null, new org.joml.Vector3f(0.35F), null));
							MemoryActor a = actors.get(id);
							if (a != null) {
								d.setPos(a.getX(), a.getY() + 1, a.getZ());
							}
							level.addFreshEntity(d);
							held.put(id, d);
						}
					}
					return true;
				}
				case "say" -> {
					if (stepTicks == 0) {
						String who = st.get("actor").getAsString();
						player.sendOverlayMessage(Component.translatable("memory.celestial.who." + who).withStyle(ChatFormatting.GOLD)
							.append(Component.literal(": ").withStyle(ChatFormatting.DARK_GRAY))
							.append(Component.translatable(st.get("key").getAsString()).withStyle(ChatFormatting.ITALIC, ChatFormatting.WHITE)));
					}
					return stepTicks >= (st.has("ticks") ? st.get("ticks").getAsInt() : 60);
				}
				case "voice" -> {
					// Глас из света: без фигуры — столб света с неба и строка в середине экрана
					if (stepTicks == 0) {
						Vec3 p = st.has("pos") ? point(st.get("pos")) : player.position();
						for (int i = 0; i < 24; i++) {
							level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + i * 0.8, p.z, 6, 0.4, 0.3, 0.4, 0.02);
						}
						dev.celestial.boss.BossIntro.title(player, Component.empty(),
							Component.translatable(st.get("key").getAsString()).withStyle(ChatFormatting.GOLD), 60);
						level.playSound(null, player.blockPosition(), SoundEvents.BEACON_ACTIVATE, SoundSource.AMBIENT, 1.2F, 0.6F);
					}
					return stepTicks >= (st.has("ticks") ? st.get("ticks").getAsInt() : 80);
				}
				case "particles" -> {
					Vec3 p = point(st.get("pos"));
					var type = BuiltInRegistries.PARTICLE_TYPE.getValue(Identifier.parse(st.get("type").getAsString()));
					if (type instanceof SimpleParticleType simple) {
						double s = st.has("spread") ? st.get("spread").getAsDouble() : 1.0;
						level.sendParticles(simple, p.x, p.y, p.z, st.has("count") ? st.get("count").getAsInt() : 20, s, s, s,
							st.has("speed") ? st.get("speed").getAsDouble() : 0.02);
					}
					return true;
				}
				case "dim" -> {
					ServerPlayNetworking.send(player, new MemoryOverlayPayload(true, st.get("value").getAsFloat()));
					return true;
				}
				case "spawn" -> {
					JsonObject ao = st.getAsJsonObject("actor");
					spawn(new MemoryScenes.Actor(ao.get("id").getAsString(), ao.get("type").getAsString(), ao.get("skin").getAsString(),
						MemoryScenes.vec(ao.get("pos")), ao.has("yaw") ? ao.get("yaw").getAsFloat() : 0.0F, ao.has("pose") ? ao.get("pose").getAsInt() : 0));
					return true;
				}
				case "entity" -> {
					// декор-сущность из реестра (например, Херувим с пламенным мечом вдали); без ИИ, неуязвима
					var type = BuiltInRegistries.ENTITY_TYPE.getValue(Identifier.parse(st.get("type").getAsString()));
					Entity e = type.create(level, EntitySpawnReason.TRIGGERED);
					if (e != null) {
						Vec3 p = point(st.get("pos"));
						e.snapTo(p.x, p.y, p.z, st.has("yaw") ? st.get("yaw").getAsFloat() : 0.0F, 0.0F);
						if (e instanceof net.minecraft.world.entity.Mob m) {
							m.setNoAi(true);
							m.setPersistenceRequired();
						}
						level.addFreshEntity(e);
						level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 1.5, p.z, 40, 1.5, 1.0, 1.5, 0.05);
						String id = st.has("id") ? st.get("id").getAsString() : "_e" + step;
						if (e instanceof MemoryActor ma) {
							actors.put(id, ma);
						} else {
							extra.add(e);
						}
					}
					return true;
				}
				case "despawn" -> {
					MemoryActor a = actors.remove(st.get("actor").getAsString());
					if (a != null) {
						level.sendParticles(ParticleTypes.END_ROD, a.getX(), a.getY() + 1, a.getZ(), 20, 0.3, 0.6, 0.3, 0.03);
						a.discard();
					}
					return true;
				}
				case "end" -> {
					return stepTicks >= (st.has("ticks") ? st.get("ticks").getAsInt() : 20);
				}
				default -> {
					Celestial.LOGGER.warn("Неизвестный шаг сцены {}: {}", scene.id(), t);
					return true;
				}
			}
		}

		final List<Entity> extra = new ArrayList<>();
	}
}
