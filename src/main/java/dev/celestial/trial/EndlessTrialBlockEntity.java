package dev.celestial.trial;

import dev.celestial.data.CelestialData;
import dev.celestial.registry.ModBlockEntities;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.scores.Objective;
import net.minecraft.world.scores.ScoreHolder;
import net.minecraft.world.scores.criteria.ObjectiveCriteria;

/**
 * Бесконечное испытание: волны без конца. Каждая волна больше и сильнее, враги идут ярусами миров (Рай → Бездна → Чертоги →
 * Хроноград → Астрал, дальше — вперемешку), каждая пятая — с чемпионом. Испытание идёт, пока рядом (24 блока) жив хоть один участник.
 * Рекорд — наибольшая пройденная волна, в таблице счёта {@code celestial_endless} (общая для мира — это и есть рейтинг);
 * ранги: 5 — Бронза, 10 — Серебро, 15 — Золото, 20 — Звезда (запись Кодекса {@code endless_rank:<n>}).
 * Ход испытания не сохраняется: после выгрузки чанка камень снова свободен.
 */
public class EndlessTrialBlockEntity extends BlockEntity {
	public static final String OBJECTIVE = "celestial_endless";
	public static final int[] RANKS = {5, 10, 15, 20};
	private static final int ARENA = 9, LEASH = 24, PAUSE = 100, MAX_ALIVE = 24;
	private static final String[][] TIERS = {
		{"fallen_guardian", "winged_serpent", "shadow"},
		{"blind_hunter", "deep_worm", "light_eater", "storm_spirit"},
		{"frost_wraith", "ice_guardian", "storm_spirit"},
		{"clockwork_sentry", "brass_doll", "ophanim"},
		{"star_devourer", "ophanim", "frost_wraith", "blind_hunter"},
	};
	private static final String[] PRIZES = {"celestial:starquartz", "celestial:etherite_ingot", "celestial:chronite_ingot", "celestial:star_stone",
		"celestial:celestite_ingot"};

	private int wave;
	private int pause;
	private boolean running;
	private final Set<UUID> fighters = new HashSet<>();
	private final Set<UUID> everyone = new HashSet<>();
	private final List<UUID> spawned = new ArrayList<>();

	public EndlessTrialBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.ENDLESS_TRIAL, pos, state);
	}

	public void start(ServerLevel level, ServerPlayer player) {
		if (running) {
			player.sendSystemMessage(Component.translatable("trial.celestial.endless.busy", wave).withStyle(ChatFormatting.GRAY));
			return;
		}
		if (!CelestialData.world(level.getServer()).has("act5_done")) {
			player.sendSystemMessage(Component.translatable("trial.celestial.endless.locked").withStyle(ChatFormatting.GRAY));
			return;
		}
		running = true;
		wave = 0;
		pause = 60;
		fighters.clear();
		everyone.clear();
		spawned.clear();
		for (ServerPlayer p : level.getEntitiesOfClass(ServerPlayer.class, new net.minecraft.world.phys.AABB(worldPosition).inflate(ARENA + 2),
				p -> p.isAlive() && !p.isSpectator())) {
			fighters.add(p.getUUID());
			everyone.add(p.getUUID());
			p.sendSystemMessage(Component.translatable("trial.celestial.endless.start").withStyle(ChatFormatting.GOLD));
		}
		level.playSound(null, worldPosition, SoundEvents.TRIAL_SPAWNER_DETECT_PLAYER, SoundSource.BLOCKS, 1.5F, 0.7F);
	}

	public static void serverTick(Level level, BlockPos pos, BlockState state, EndlessTrialBlockEntity be) {
		if (be.running && level instanceof ServerLevel server) {
			be.tick(server);
		}
	}

	private void tick(ServerLevel level) {
		fighters.removeIf(id -> {
			ServerPlayer p = level.getServer().getPlayerList().getPlayer(id);
			return p == null || !p.isAlive() || p.level() != level || p.distanceToSqr(net.minecraft.world.phys.Vec3.atCenterOf(worldPosition)) > LEASH * LEASH;
		});
		if (fighters.isEmpty()) {
			finish(level);
			return;
		}
		if (pause > 0) {
			if (--pause == 0) {
				spawnWave(level, ++wave);
			}
			return;
		}
		if (level.getGameTime() % 10 != 0) {
			return;
		}
		spawned.removeIf(id -> {
			Entity e = level.getEntity(id);
			if (e != null && e.isAlive() && e.distanceToSqr(net.minecraft.world.phys.Vec3.atCenterOf(worldPosition)) > (LEASH + 8) * (LEASH + 8)) {
				e.discard();  // ушёл далеко или застрял за ареной — не тянуть волну вечно
				return true;
			}
			return e == null || !e.isAlive();
		});
		if (spawned.isEmpty()) {
			cleared(level);
		}
	}

	private void spawnWave(ServerLevel level, int n) {
		int tier = Math.min(TIERS.length - 1, (n - 1) / 3);
		int count = Math.min(MAX_ALIVE, 2 + n + n / 3);
		var random = level.getRandom();
		for (int i = 0; i < count; i++) {
			String[] pool = n > 15 ? TIERS[random.nextInt(TIERS.length)] : TIERS[tier];
			spawn(level, pool[random.nextInt(pool.length)], n, false);
		}
		if (n % 5 == 0) {
			String[] pool = TIERS[tier];
			spawn(level, pool[random.nextInt(pool.length)], n, true);
		}
		for (UUID id : fighters) {
			ServerPlayer p = level.getServer().getPlayerList().getPlayer(id);
			if (p != null) {
				dev.celestial.boss.BossIntro.title(p, Component.translatable("trial.celestial.endless.wave", n).withStyle(ChatFormatting.GOLD),
					Component.translatable(n % 5 == 0 ? "trial.celestial.endless.champion" : "trial.celestial.endless.foes", count), 40);
			}
		}
		level.playSound(null, worldPosition, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 2.0F, 1.0F + Math.min(0.6F, n * 0.03F));
	}

	private void spawn(ServerLevel level, String id, int n, boolean champion) {
		EntityType<?> type = BuiltInRegistries.ENTITY_TYPE.getValue(Identifier.fromNamespaceAndPath("celestial", id));
		Entity e = type.create(level, EntitySpawnReason.TRIAL_SPAWNER);
		if (e == null) {
			return;
		}
		var random = level.getRandom();
		BlockPos at = null;
		for (int tries = 0; tries < 12 && at == null; tries++) {
			double a = random.nextDouble() * Math.PI * 2, r = 3 + random.nextDouble() * (ARENA - 3);
			BlockPos column = BlockPos.containing(worldPosition.getX() + 0.5 + Math.cos(a) * r, worldPosition.getY(), worldPosition.getZ() + 0.5 + Math.sin(a) * r);
			for (int dy = 3; dy >= -3; dy--) {
				BlockPos p = column.above(dy);
				if (level.getBlockState(p.below()).isFaceSturdy(level, p.below(), net.minecraft.core.Direction.UP)
						&& level.getBlockState(p).getCollisionShape(level, p).isEmpty() && level.getBlockState(p.above()).getCollisionShape(level, p.above()).isEmpty()) {
					at = p;
					break;
				}
			}
		}
		if (at == null) {
			at = worldPosition.above();
		}
		e.snapTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, random.nextFloat() * 360, 0);
		e.addTag(dev.celestial.world.abyss.Darkness.NO_REPEL);
		if (e instanceof Mob mob) {
			mob.finalizeSpawn(level, level.getCurrentDifficultyAt(at), EntitySpawnReason.TRIAL_SPAWNER, null);
			mob.setPersistenceRequired();
			double scale = 1.0 + 0.08 * n + (champion ? 2.0 : 0.0);
			var hp = mob.getAttribute(Attributes.MAX_HEALTH);
			if (hp != null) {
				hp.setBaseValue(Math.min(1000.0, hp.getBaseValue() * scale));
				mob.setHealth(mob.getMaxHealth());
			}
			if (n >= 6) {
				mob.addEffect(new MobEffectInstance(MobEffects.STRENGTH, -1, Math.min(4, n / 6 - 1 + (champion ? 1 : 0))));
			}
			if (champion) {
				mob.setGlowingTag(true);
				mob.setCustomName(Component.translatable("trial.celestial.endless.champion_name", mob.getType().getDescription()).withStyle(ChatFormatting.GOLD));
			}
			ServerPlayer target = nearestFighter(level, e);
			if (target != null) {
				mob.setTarget(target);
			}
		}
		level.addFreshEntity(e);
		level.sendParticles(ParticleTypes.TRIAL_SPAWNER_DETECTED_PLAYER, e.getX(), e.getY() + 0.5, e.getZ(), 15, 0.3, 0.5, 0.3, 0.01);
		spawned.add(e.getUUID());
	}

	private ServerPlayer nearestFighter(ServerLevel level, Entity e) {
		ServerPlayer best = null;
		for (UUID id : fighters) {
			ServerPlayer p = level.getServer().getPlayerList().getPlayer(id);
			if (p != null && (best == null || p.distanceToSqr(e) < best.distanceToSqr(e))) {
				best = p;
			}
		}
		return best;
	}

	private void cleared(ServerLevel level) {
		pause = PAUSE;
		for (UUID id : fighters) {
			ServerPlayer p = level.getServer().getPlayerList().getPlayer(id);
			if (p == null) {
				continue;
			}
			p.giveExperiencePoints(5 * wave);
			p.sendSystemMessage(Component.translatable("trial.celestial.endless.cleared", wave).withStyle(ChatFormatting.YELLOW));
			if (wave % 5 == 0) {
				Item prize = BuiltInRegistries.ITEM.getValue(Identifier.parse(PRIZES[Math.min(PRIZES.length - 1, wave / 5 - 1)]));
				ItemStack stack = new ItemStack(prize, 1 + wave / 5);
				if (!p.getInventory().add(stack)) {
					p.spawnAtLocation(level, stack);
				}
				CelestialData.update(p, d -> d.withGrace(d.grace() + 1));
			}
			record(level, p, wave);
		}
		level.sendParticles(ParticleTypes.END_ROD, worldPosition.getX() + 0.5, worldPosition.getY() + 1.5, worldPosition.getZ() + 0.5, 40, 0.4, 0.8, 0.4, 0.05);
		level.playSound(null, worldPosition, SoundEvents.TRIAL_SPAWNER_EJECT_ITEM, SoundSource.BLOCKS, 1.2F, 1.0F);
	}

	/** Рекорд игрока: наибольшая пройденная волна; новый ранг — титр. */
	public static void record(ServerLevel level, ServerPlayer p, int reached) {
		var board = level.getServer().getScoreboard();
		Objective obj = board.getObjective(OBJECTIVE);
		if (obj == null) {
			obj = board.addObjective(OBJECTIVE, ObjectiveCriteria.DUMMY, Component.translatable("trial.celestial.endless.objective"),
				ObjectiveCriteria.RenderType.INTEGER, false, null);
		}
		var score = board.getOrCreatePlayerScore(ScoreHolder.forNameOnly(p.getScoreboardName()), obj);
		if (reached > score.get()) {
			score.set(reached);
		}
		if (reached >= 5) {
			dev.celestial.story.Story.ENDLESS_BRONZE.grant(p);
		}
		if (reached >= 20) {
			dev.celestial.story.Story.ENDLESS_STAR.grant(p);
		}
		for (int i = RANKS.length - 1; i >= 0; i--) {
			int rank = RANKS[i];
			if (reached >= rank && !CelestialData.get(p).knows("endless_rank:" + rank)) {
				CelestialData.update(p, d -> d.withCodex("endless_rank:" + rank));
				dev.celestial.boss.BossIntro.title(p, Component.translatable("trial.celestial.endless.rank." + rank).withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD),
					Component.translatable("trial.celestial.endless.rank_sub", rank).withStyle(ChatFormatting.ITALIC), 80);
				break;
			}
		}
	}

	private void finish(ServerLevel level) {
		int reached = Math.max(0, pause > 0 ? wave : wave - 1);
		for (UUID id : spawned) {
			Entity e = level.getEntity(id);
			if (e != null) {
				level.sendParticles(ParticleTypes.POOF, e.getX(), e.getY() + 0.5, e.getZ(), 10, 0.3, 0.4, 0.3, 0.02);
				e.discard();
			}
		}
		for (UUID id : everyone) {
			ServerPlayer p = level.getServer().getPlayerList().getPlayer(id);
			if (p != null) {
				int best = level.getServer().getScoreboard().getObjective(OBJECTIVE) == null ? reached
					: level.getServer().getScoreboard().getOrCreatePlayerScore(ScoreHolder.forNameOnly(p.getScoreboardName()),
						level.getServer().getScoreboard().getObjective(OBJECTIVE)).get();
				p.sendSystemMessage(Component.translatable("trial.celestial.endless.over", reached, Math.max(best, reached)).withStyle(ChatFormatting.GOLD));
			}
		}
		running = false;
		wave = 0;
		pause = 0;
		fighters.clear();
		everyone.clear();
		spawned.clear();
	}

	/** Для сценариев и отладки. */
	public boolean running() {
		return running;
	}

	public int wave() {
		return wave;
	}
}
