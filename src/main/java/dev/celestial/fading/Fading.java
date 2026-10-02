package dev.celestial.fading;

import dev.celestial.Celestial;
import dev.celestial.data.CelestialData;
import dev.celestial.data.WorldState;
import dev.celestial.registry.ModEntities;
import dev.celestial.registry.ModGameRules;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.clock.WorldClock;
import net.minecraft.world.clock.WorldClocks;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

/**
 * Угасание Верхнего мира: стадия 0–5 растёт раз в N дней (правило celestial:fading_days) и падает за пройденные акты.
 * Стадии удлиняют ночи (часы идут медленнее), усиливают монстров, с 3-й ночью приходят Тени. Ночами падают метеориты.
 * Всё отключается правилом celestial:fading (метеориты — celestial:meteors).
 */
public final class Fading {
	private static final Identifier HEALTH = Celestial.id("fading_health");
	private static final Identifier DAMAGE = Celestial.id("fading_damage");
	private static final int NIGHT_START = 13000;
	private static final int NIGHT_END = 23000;

	private Fading() {}

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(Fading::tick);
		ServerEntityEvents.ENTITY_LOAD.register(Fading::onEntityLoad);
	}

	public static boolean enabled(MinecraftServer server) {
		return server.overworld().getGameRules().get(ModGameRules.FADING);
	}

	/** Действующая стадия (0, если механика выключена). */
	public static int stage(MinecraftServer server) {
		return enabled(server) ? CelestialData.world(server).fading() : 0;
	}

	/** Предел стадии: каждый пройденный акт снимает одну ступень. */
	public static int cap(WorldState state) {
		return Math.max(0, WorldState.MAX_FADING - state.act());
	}

	public static boolean isNight(ServerLevel overworld) {
		long time = overworld.getOverworldClockTime() % 24000L;
		return time >= NIGHT_START && time < NIGHT_END;
	}

	private static void tick(MinecraftServer server) {
		ServerLevel overworld = server.overworld();
		long gameTime = overworld.getGameTime();
		if (gameTime % 20 != 0) {
			return;
		}
		boolean enabled = enabled(server);
		updateNightLength(overworld, enabled);
		if (!enabled) {
			return;
		}
		progress(server, overworld);
		boolean night = isNight(overworld);
		int stage = CelestialData.world(server).fading();
		if (night && gameTime % 200 == 0) {
			for (ServerPlayer player : overworld.players()) {
				if (!player.isSpectator()) {
					Meteors.maybeFall(overworld, player, stage);
					if (stage >= 3) {
						spawnShadows(overworld, player, stage);
					}
				}
			}
		}
	}

	/** Длинные ночи: на стадии N ночь тянется в 1 + 0.2·N раза дольше. */
	private static void updateNightLength(ServerLevel overworld, boolean enabled) {
		Holder<WorldClock> clock = overworld.registryAccess().lookupOrThrow(Registries.WORLD_CLOCK).getOrThrow(WorldClocks.OVERWORLD);
		float rate = 1.0F;
		if (enabled && isNight(overworld)) {
			rate = 1.0F / (1.0F + 0.2F * CelestialData.world(overworld.getServer()).fading());
		}
		var manager = overworld.clockManager();
		if (Math.abs(manager.getInstance(clock).rate() - rate) > 1.0E-4F) {
			manager.setRate(clock, rate);
		}
	}

	/** Раз в fading_days дней стадия растёт (до предела по актам). */
	private static void progress(MinecraftServer server, ServerLevel overworld) {
		long day = overworld.getOverworldClockTime() / 24000L;
		WorldState state = CelestialData.world(server);
		if (state.lastFadingDay() == 0L || day < state.lastFadingDay()) {
			CelestialData.updateWorld(server, s -> s.withLastFadingDay(Math.max(1L, day)));
			return;
		}
		int every = overworld.getGameRules().get(ModGameRules.FADING_DAYS);
		if (day - state.lastFadingDay() >= every) {
			boolean grows = state.fading() < cap(state);
			WorldState next = CelestialData.updateWorld(server, s -> (grows ? s.withFading(s.fading() + 1) : s).withLastFadingDay(day));
			if (grows) {
				announce(server, Component.translatable("fading.celestial.grow." + next.fading()));
			}
		}
	}

	/** Сюжет снизил Угасание (пройден акт). */
	public static void weaken(MinecraftServer server, int stages) {
		WorldState next = CelestialData.updateWorld(server, s -> s.withFading(s.fading() - stages));
		announce(server, Component.translatable("fading.celestial.weaken", next.fading()));
	}

	private static void announce(MinecraftServer server, Component message) {
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			player.sendSystemMessage(message);
			player.level().playSound(null, player.blockPosition(), SoundEvents.AMBIENT_CAVE.value(), SoundSource.AMBIENT, 1.0F, 0.6F);
		}
	}

	/** Монстры Верхнего мира получают +10% здоровья и урона за стадию. */
	private static void onEntityLoad(Entity entity, ServerLevel level) {
		if (!(entity instanceof LivingEntity living) || !(entity instanceof Enemy) || level != level.getServer().overworld()) {
			return;
		}
		int stage = stage(level.getServer());
		boolean fresh = living.tickCount == 0 && living.getHealth() >= living.getMaxHealth();
		apply(living.getAttribute(Attributes.MAX_HEALTH), HEALTH, 0.1 * stage);
		apply(living.getAttribute(Attributes.ATTACK_DAMAGE), DAMAGE, 0.1 * stage);
		if (fresh) {
			living.setHealth(living.getMaxHealth());
		}
	}

	private static void apply(AttributeInstance attribute, Identifier id, double amount) {
		if (attribute == null) {
			return;
		}
		if (amount <= 0) {
			attribute.removeModifier(id);
		} else {
			attribute.addOrReplacePermanentModifier(new AttributeModifier(id, amount, AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
		}
	}

	/** Тени приходят во тьме вокруг игрока: не больше (стадия − 1) рядом. */
	private static void spawnShadows(ServerLevel level, ServerPlayer player, int stage) {
		RandomSource random = level.getRandom();
		if (random.nextFloat() > 0.35F) {
			return;
		}
		int near = level.getEntities(ModEntities.SHADOW, player.getBoundingBox().inflate(48), e -> true).size();
		if (near >= stage - 1) {
			return;
		}
		double angle = random.nextDouble() * Math.PI * 2;
		int dist = Mth.nextInt(random, 18, 36);
		int x = Mth.floor(player.getX() + Math.cos(angle) * dist);
		int z = Mth.floor(player.getZ() + Math.sin(angle) * dist);
		if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
			return;
		}
		BlockPos pos = new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
		if (level.getBrightness(LightLayer.BLOCK, pos) > 6 || !level.getFluidState(pos.below()).isEmpty() || level.getFluidState(pos).isSource()) {
			return;
		}
		Shadow shadow = ModEntities.SHADOW.spawn(level, pos, EntitySpawnReason.EVENT);
		if (shadow != null) {
			level.sendParticles(net.minecraft.core.particles.ParticleTypes.LARGE_SMOKE, pos.getX() + 0.5, pos.getY() + 1, pos.getZ() + 0.5, 20, 0.3, 0.8, 0.3, 0.01);
		}
	}

	static Vec3 horizontal(RandomSource random, double min, double max) {
		double angle = random.nextDouble() * Math.PI * 2;
		double dist = min + random.nextDouble() * (max - min);
		return new Vec3(Math.cos(angle) * dist, 0, Math.sin(angle) * dist);
	}
}
