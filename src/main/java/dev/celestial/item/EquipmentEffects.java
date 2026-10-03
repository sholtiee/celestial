package dev.celestial.item;

import dev.celestial.Celestial;
import dev.celestial.registry.ModItems;
import dev.celestial.world.HeavenDimension;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.core.Holder;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;

/** Пассивные эффекты экипировки Рая: нимб, полный комплект эфирита, облачный парашют. */
public final class EquipmentEffects {
	private static final Identifier SET_SAFE_FALL = Celestial.id("etherite_set_safe_fall");
	private static final Identifier SET_SPEED = Celestial.id("etherite_set_heaven_speed");
	private static final double PARACHUTE_FALL = 10.0;

	private EquipmentEffects() {}

	/** Множитель роста страха в Бездне от снаряжения (комплект безднового обсидиана — вдвое меньше). */
	public static float fearMultiplier(ServerPlayer player) {
		return hasAbyssalSet(player) ? 0.5F : 1.0F;
	}

	public static boolean hasAbyssalSet(ServerPlayer player) {
		return player.getItemBySlot(EquipmentSlot.HEAD).is(ModItems.ABYSSAL_HELMET)
			&& player.getItemBySlot(EquipmentSlot.CHEST).is(ModItems.ABYSSAL_CHESTPLATE)
			&& player.getItemBySlot(EquipmentSlot.LEGS).is(ModItems.ABYSSAL_LEGGINGS)
			&& player.getItemBySlot(EquipmentSlot.FEET).is(ModItems.ABYSSAL_BOOTS);
	}

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(EquipmentEffects::tick);
	}

	private static void tick(MinecraftServer server) {
		boolean everySecond = server.getTickCount() % 20 == 0;
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			if (player.isSpectator()) {
				continue;
			}
			checkParachute(player);
			if (everySecond) {
				haloEffects(player);
				etheriteSet(player);
			}
		}
	}

	private static void haloEffects(ServerPlayer player) {
		if (!player.getItemBySlot(EquipmentSlot.HEAD).is(ModItems.HALO)) {
			return;
		}
		refresh(player, MobEffects.REGENERATION, 0, 60);
		refresh(player, MobEffects.NIGHT_VISION, 0, 300);
	}

	private static void refresh(ServerPlayer player, Holder<MobEffect> effect, int amplifier, int duration) {
		MobEffectInstance current = player.getEffect(effect);
		if (current == null || current.getDuration() < duration - 40) {
			player.addEffect(new MobEffectInstance(effect, duration, amplifier, true, false, true));
		}
	}

	/** Полный комплект эфирита: падение не страшно, а в Раю ещё и быстрее бег. */
	private static void etheriteSet(ServerPlayer player) {
		boolean fullSet = player.getItemBySlot(EquipmentSlot.HEAD).is(ModItems.ETHERITE_HELMET)
			&& player.getItemBySlot(EquipmentSlot.CHEST).is(ModItems.ETHERITE_CHESTPLATE)
			&& player.getItemBySlot(EquipmentSlot.LEGS).is(ModItems.ETHERITE_LEGGINGS)
			&& player.getItemBySlot(EquipmentSlot.FEET).is(ModItems.ETHERITE_BOOTS);
		toggle(player.getAttribute(Attributes.SAFE_FALL_DISTANCE),
			new AttributeModifier(SET_SAFE_FALL, 256.0, AttributeModifier.Operation.ADD_VALUE), fullSet);
		toggle(player.getAttribute(Attributes.MOVEMENT_SPEED),
			new AttributeModifier(SET_SPEED, 0.15, AttributeModifier.Operation.ADD_MULTIPLIED_BASE), fullSet && HeavenDimension.isHeaven(player.level()));
	}

	private static void toggle(AttributeInstance attribute, AttributeModifier modifier, boolean enabled) {
		if (attribute == null) {
			return;
		}
		boolean has = attribute.hasModifier(modifier.id());
		if (enabled && !has) {
			attribute.addTransientModifier(modifier);
		} else if (!enabled && has) {
			attribute.removeModifier(modifier.id());
		}
	}

	/** Парашют раскрывается сам, если игрок падает слишком долго и у него нет крыльев. */
	private static void checkParachute(ServerPlayer player) {
		if (player.getAbilities().flying || player.isFallFlying() || player.onGround() || player.isInWater()
			|| player.fallDistance < PARACHUTE_FALL || player.getDeltaMovement().y > -0.5 || player.hasEffect(MobEffects.SLOW_FALLING)) {
			return;
		}
		var inventory = player.getInventory();
		for (int i = 0; i < inventory.getContainerSize(); i++) {
			ItemStack stack = inventory.getItem(i);
			if (stack.is(ModItems.CLOUD_PARACHUTE)) {
				if (!player.getAbilities().instabuild) {
					stack.shrink(1);
				}
				player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 20 * 12, 0, false, true, true));
				player.resetFallDistance();
				player.level().playSound(null, player.blockPosition(), SoundEvents.WOOL_PLACE, SoundSource.PLAYERS, 1.0F, 0.8F);
				player.level().sendParticles(ParticleTypes.CLOUD, player.getX(), player.getY() + 2.2, player.getZ(), 30, 0.8, 0.2, 0.8, 0.02);
				return;
			}
		}
	}
}
