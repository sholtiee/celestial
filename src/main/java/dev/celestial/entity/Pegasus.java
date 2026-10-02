package dev.celestial.entity;

import dev.celestial.registry.ModEntities;
import dev.celestial.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.animal.equine.AbstractHorse;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/** Пегас: приручается манной, под седлом летает — удерживай прыжок, чтобы набрать высоту. */
public class Pegasus extends AbstractHorse {
	private static final double LIFT = 0.09, MAX_CLIMB = 0.42, GLIDE_FALL = -0.12;

	public Pegasus(EntityType<? extends Pegasus> type, Level level) {
		super(type, level);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return createBaseHorseAttributes()
			.add(Attributes.MAX_HEALTH, 40.0)
			.add(Attributes.MOVEMENT_SPEED, 0.3)
			.add(Attributes.JUMP_STRENGTH, 0.9)
			.add(Attributes.SAFE_FALL_DISTANCE, 64.0);
	}

	@Override
	public boolean isFood(ItemStack stack) {
		return stack.is(ModItems.MANNA_BERRIES);
	}

	@Override
	protected boolean handleEating(Player player, ItemStack stack) {
		if (!stack.is(ModItems.MANNA_BERRIES)) {
			return super.handleEating(player, stack);
		}
		boolean used = false;
		if (getHealth() < getMaxHealth()) {
			heal(4.0F);
			used = true;
		}
		if (!isTamed() && getTemper() < getMaxTemper()) {
			modifyTemper(8);
			used = true;
		}
		if (!level().isClientSide() && isTamed() && getAge() == 0 && !isInLove()) {
			setInLove(player);
			used = true;
		}
		if (used) {
			playSound(SoundEvents.HORSE_EAT, 1.0F, 1.2F);
		}
		return used;
	}

	@Override
	protected void tickRidden(Player controller, Vec3 riddenInput) {
		super.tickRidden(controller, riddenInput);
		if (!isLocalInstanceAuthoritative() || !isSaddled()) {
			return;
		}
		Vec3 motion = getDeltaMovement();
		if (controller.isJumping() && !onGround()) {
			// взмах крыльями: набираем высоту
			setDeltaMovement(motion.x, Math.min(motion.y + LIFT, MAX_CLIMB), motion.z);
		} else if (!onGround() && motion.y < GLIDE_FALL) {
			// без прыжка — плавно планируем
			setDeltaMovement(motion.x, GLIDE_FALL, motion.z);
		}
		resetFallDistance();
	}

	@Override
	protected float getRiddenSpeed(Player controller) {
		float base = super.getRiddenSpeed(controller);
		return onGround() ? base : base * 1.6F;
	}

	@Override
	public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
		return false;
	}

	@Override
	protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {
	}

	@Override
	public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
		return partner instanceof Pegasus ? ModEntities.PEGASUS.create(level, EntitySpawnReason.BREEDING) : null;
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return SoundEvents.HORSE_AMBIENT;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.HORSE_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.HORSE_DEATH;
	}

	@Override
	public float getVoicePitch() {
		return 1.3F;
	}
}
