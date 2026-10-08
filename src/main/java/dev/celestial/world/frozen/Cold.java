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
			delta *= 1.0F - insulation(player);
			if (player.getVehicle() instanceof dev.celestial.entity.IceWolf) {  // густая шерсть ледяного волка греет седока
				delta *= 0.5F;
			}
			if (data.hasSkill(Skill.INNER_FIRE.id)) {
				delta *= 0.5F;
			}
		}
		boolean crown = dev.celestial.item.EquipmentEffects.wearsIceCrown(player);
		if (crown) {  // Корона Архонта: холод над носителем не властен — тепло само возвращается
			delta = Math.max(delta, 2.0F);
		} else if (player.hasEffect(dev.celestial.registry.ModEffects.WARMED)) {  // горячая еда: тепло не тает
			delta = Math.max(delta, 0.0F);
		}
		final float change = delta;
		float warmth = CelestialData.update(player, d -> d.withWarmth(d.warmth() + change)).warmth();
		if (warmth < 30) {
			player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 0, true, false, false));
			if (data.warmth() >= 30) {
				player.sendOverlayMessage(Component.translatable("frozen.celestial.cold_rising"));
			}
		}
		if (warmth <= 0 && !hasFrostSet(player) && !crown) {
			player.setTicksFrozen(Math.max(player.getTicksFrozen(), player.getTicksRequiredToFreeze() + 40));
			// ванильный урон мороза не идёт, если надет любой предмет из #freeze_immune_wearables (вся кожа) — бьём сами
			if (!player.canFreeze()) {
				player.hurtServer(level, level.damageSources().freeze(), 1.0F);
			}
		}
	}

	/** Насколько одежда сберегает тепло: кожа −12% за предмет, мех снежного лиса −22% (полный меховой комплект почти не мёрзнет). */
	public static float insulation(ServerPlayer player) {
		float total = 0;
		for (EquipmentSlot slot : new EquipmentSlot[] {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET}) {
			var stack = player.getItemBySlot(slot);
			if (stack.is(dev.celestial.registry.ModItems.FUR_HOOD) || stack.is(dev.celestial.registry.ModItems.FUR_CLOAK)
				|| stack.is(dev.celestial.registry.ModItems.FUR_LEGGINGS) || stack.is(dev.celestial.registry.ModItems.FUR_BOOTS)) {
				total += 0.22F;
			} else if (stack.is(dev.celestial.registry.ModItems.FROST_HELMET) || stack.is(dev.celestial.registry.ModItems.FROST_CHESTPLATE)
				|| stack.is(dev.celestial.registry.ModItems.FROST_LEGGINGS) || stack.is(dev.celestial.registry.ModItems.FROST_BOOTS)) {
				total += 0.15F;
			} else if (stack.is(Items.LEATHER_HELMET) || stack.is(Items.LEATHER_CHESTPLATE) || stack.is(Items.LEATHER_LEGGINGS)
				|| stack.is(Items.LEATHER_BOOTS)) {
				total += 0.12F;
			}
		}
		return Math.min(0.9F, total);
	}

	/** Полный комплект морозной стали: не замерзает (тепло всё равно тает, но иней не наступает). */
	public static boolean hasFrostSet(ServerPlayer player) {
		return player.getItemBySlot(EquipmentSlot.HEAD).is(dev.celestial.registry.ModItems.FROST_HELMET)
			&& player.getItemBySlot(EquipmentSlot.CHEST).is(dev.celestial.registry.ModItems.FROST_CHESTPLATE)
			&& player.getItemBySlot(EquipmentSlot.LEGS).is(dev.celestial.registry.ModItems.FROST_LEGGINGS)
			&& player.getItemBySlot(EquipmentSlot.FEET).is(dev.celestial.registry.ModItems.FROST_BOOTS);
	}

	/** Огонь рядом: костёр (горящий), огонь, лава, магма, горящая жаровня — в радиусе 4. */
	public static boolean nearHeat(ServerLevel level, BlockPos center) {
		for (BlockPos p : BlockPos.betweenClosed(center.offset(-4, -2, -4), center.offset(4, 3, 4))) {
			BlockState s = level.getBlockState(p);
			if (s.is(BlockTags.FIRE) || s.is(net.minecraft.world.level.block.Blocks.LAVA) || s.is(net.minecraft.world.level.block.Blocks.MAGMA_BLOCK)
				|| s.getBlock() instanceof CampfireBlock && s.getValue(CampfireBlock.LIT)
				|| s.getBlock() instanceof dev.celestial.block.BurningBushBlock
				|| s.getBlock() instanceof dev.celestial.boss.BrazierBlock && s.getValue(dev.celestial.boss.BrazierBlock.LIT)) {
				return true;
			}
		}
		return false;
	}
}
