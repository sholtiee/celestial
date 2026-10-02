package dev.celestial.world.abyss;

import dev.celestial.Celestial;
import dev.celestial.data.CelestialData;
import dev.celestial.data.PlayerData;
import dev.celestial.grace.Skill;
import dev.celestial.registry.ModSounds;
import dev.celestial.world.dim.AbyssFeatures;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.TagKey;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LightBlock;

/**
 * Тьма Бездны. Раз в секунду: если у глаз светло (блочный свет ≥ 6) или в руке источник света — страх падает,
 * иначе растёт. 50+ — пульсирует Тьма, 80+ — замедление и шёпот, 100 — тьма ранит.
 * Динамический свет: игроку с источником света в руке ставим невидимый блок света у головы и переносим за ним.
 */
public final class Darkness {
	public static final TagKey<Item> LIGHT_SOURCES = TagKey.create(Registries.ITEM, Celestial.id("light_sources"));
	public static final ResourceKey<DamageType> DAMAGE = ResourceKey.create(Registries.DAMAGE_TYPE, Celestial.id("darkness"));
	private static final int LIGHT_LEVEL = 13;
	private static final Map<UUID, LightSpot> LIGHTS = new HashMap<>();

	private record LightSpot(ServerLevel level, BlockPos pos) {}

	private Darkness() {}

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(Darkness::tick);
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> clearLight(handler.player.getUUID()));
	}

	public static boolean inAbyss(ServerPlayer player) {
		return player.level().dimension() == AbyssFeatures.ABYSS;
	}

	public static boolean holdsLight(ServerPlayer player) {
		return player.getMainHandItem().is(LIGHT_SOURCES) || player.getOffhandItem().is(LIGHT_SOURCES);
	}

	private static void tick(MinecraftServer server) {
		long time = server.overworld().getGameTime();
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			if (time % 2 == 0) {
				updateLight(player);
			}
			if (time % 20 == 0) {
				updateFear(player);
			}
		}
	}

	private static void updateFear(ServerPlayer player) {
		PlayerData data = CelestialData.get(player);
		boolean affected = inAbyss(player) && !player.isCreative() && !player.isSpectator();
		if (!affected) {
			if (data.fear() > 0) {
				CelestialData.update(player, d -> d.withFear(d.fear() - 10));
			}
			return;
		}
		BlockPos eyes = BlockPos.containing(player.getEyePosition());
		boolean lit = holdsLight(player) || player.level().getBrightness(LightLayer.BLOCK, eyes) >= 6;
		float gain = lit ? -8.0F : 4.0F;
		if (!lit) {
			if (data.hasSkill(Skill.INNER_LIGHT.id)) {
				gain *= 0.5F;
			}
			gain *= dev.celestial.item.EquipmentEffects.fearMultiplier(player);
			if (player.hasEffect(dev.celestial.registry.ModEffects.STARLIGHT)) {
				gain = 0.0F;
			}
		}
		final float delta = gain;
		float fear = CelestialData.update(player, d -> d.withFear(d.fear() + delta)).fear();
		if (fear >= 50) {
			player.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 60, 0, true, false, false));
		}
		if (fear >= 80) {
			player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 0, true, false, false));
			if (player.getRandom().nextInt(4) == 0) {
				player.level().playSound(null, player.blockPosition(), ModSounds.SHADOW_AMBIENT, SoundSource.AMBIENT, 0.6F, 0.8F + player.getRandom().nextFloat() * 0.4F);
			}
		}
		if (fear >= PlayerData.MAX_FEAR && player.level().getGameTime() % 40 == 0) {
			ServerLevel level = player.level();
			player.hurtServer(level, new DamageSource(level.registryAccess().lookupOrThrow(Registries.DAMAGE_TYPE).getOrThrow(DAMAGE)), 2.0F);
		}
		if (fear >= 50 && data.fear() < 50) {
			player.sendOverlayMessage(Component.translatable("abyss.celestial.fear_rising"));
		}
	}

	/** Блок света у головы игрока с источником света в руке (только в Бездне). */
	private static void updateLight(ServerPlayer player) {
		UUID id = player.getUUID();
		LightSpot current = LIGHTS.get(id);
		if (!inAbyss(player) || !holdsLight(player) || player.isSpectator()) {
			if (current != null) {
				clearLight(id);
			}
			return;
		}
		BlockPos target = BlockPos.containing(player.getEyePosition());
		ServerLevel level = player.level();
		if (current != null && current.level == level && current.pos.equals(target)) {
			return;
		}
		if (!level.getBlockState(target).isAir()) {
			target = target.below();
			if (!level.getBlockState(target).isAir()) {
				return;
			}
		}
		clearLight(id);
		level.setBlock(target, Blocks.LIGHT.defaultBlockState().setValue(LightBlock.LEVEL, LIGHT_LEVEL), 3);
		LIGHTS.put(id, new LightSpot(level, target));
	}

	private static void clearLight(UUID id) {
		LightSpot spot = LIGHTS.remove(id);
		if (spot != null && spot.level.getBlockState(spot.pos).is(Blocks.LIGHT)) {
			spot.level.setBlock(spot.pos, Blocks.AIR.defaultBlockState(), 3);
		}
	}
}
