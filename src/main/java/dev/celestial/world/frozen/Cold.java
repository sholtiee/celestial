package dev.celestial.world.frozen;

import dev.celestial.data.CelestialData;
import dev.celestial.data.PlayerData;
import dev.celestial.grace.Skill;
import dev.celestial.world.dim.AbyssFeatures;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.CampfireBlock;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Холод Ледяных Чертогов. Раз в секунду: у огня (костёр, огонь, лава, магма, горящая жаровня в радиусе 4) — тепло
 * растёт, иначе тает: в воде и в метель быстрее, кожаная одежда и навык «Внутренний огонь» — медленнее.
 * Ниже 30 — замедление, на нуле — ванильное замерзание (иней на экране и урон).
 */
public final class Cold {
	private Cold() {}

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(Cold::tick);
	}

	public static boolean inFrozenHalls(ServerPlayer player) {
		return player.level().dimension() == AbyssFeatures.FROZEN_HALLS;
	}

	private static void tick(MinecraftServer server) {
		if (server.overworld().getGameTime() % 20 != 0) {
			return;
		}
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			update(player);
		}
	}

	private static void update(ServerPlayer player) {
		PlayerData data = CelestialData.get(player);
		boolean affected = inFrozenHalls(player) && !player.isCreative() && !player.isSpectator();
		if (!affected) {
			if (data.warmth() < 100) {
				CelestialData.update(player, d -> d.withWarmth(d.warmth() + 10));
			}
			return;
		}
		ServerLevel level = player.level();
		float delta;
		if (nearHeat(level, player.blockPosition())) {
			delta = 10.0F;
		} else {
			delta = -2.0F;
			if (player.isInWater()) {
				delta -= 4.0F;
			}
			if (level.isRaining()) {  // в Чертогах дождь — это метель
				delta -= 1.0F;
				player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 0, true, false, false));
			}
			delta *= 1.0F - 0.2F * leatherPieces(player);
			if (data.hasSkill(Skill.INNER_FIRE.id)) {
				delta *= 0.5F;
			}
		}
		final float change = delta;
		float warmth = CelestialData.update(player, d -> d.withWarmth(d.warmth() + change)).warmth();
		if (warmth < 30) {
			player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 0, true, false, false));
			if (data.warmth() >= 30) {
				player.sendOverlayMessage(Component.translatable("frozen.celestial.cold_rising"));
			}
		}
		if (warmth <= 0) {
			player.setTicksFrozen(Math.max(player.getTicksFrozen(), player.getTicksRequiredToFreeze() + 40));
		}
	}

	private static int leatherPieces(ServerPlayer player) {
		int n = 0;
		for (EquipmentSlot slot : new EquipmentSlot[] {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET}) {
			var stack = player.getItemBySlot(slot);
			if (stack.is(Items.LEATHER_HELMET) || stack.is(Items.LEATHER_CHESTPLATE) || stack.is(Items.LEATHER_LEGGINGS) || stack.is(Items.LEATHER_BOOTS)) {
				n++;
			}
		}
		return n;
	}

	/** Огонь рядом: костёр (горящий), огонь, лава, магма, горящая жаровня — в радиусе 4. */
	public static boolean nearHeat(ServerLevel level, BlockPos center) {
		for (BlockPos p : BlockPos.betweenClosed(center.offset(-4, -2, -4), center.offset(4, 3, 4))) {
			BlockState s = level.getBlockState(p);
			if (s.is(BlockTags.FIRE) || s.is(net.minecraft.world.level.block.Blocks.LAVA) || s.is(net.minecraft.world.level.block.Blocks.MAGMA_BLOCK)
				|| s.getBlock() instanceof CampfireBlock && s.getValue(CampfireBlock.LIT)
				|| s.getBlock() instanceof dev.celestial.boss.BrazierBlock && s.getValue(dev.celestial.boss.BrazierBlock.LIT)) {
				return true;
			}
		}
		return false;
	}
}
