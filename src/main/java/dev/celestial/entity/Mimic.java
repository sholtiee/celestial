package dev.celestial.entity;

import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** Мимик: притворяется сундуком в руинах. Просыпается, если подойти вплотную или ударить. */
public class Mimic extends Monster {
	private static final EntityDataAccessor<Boolean> AWAKE = SynchedEntityData.defineId(Mimic.class, EntityDataSerializers.BOOLEAN);
	private static final double WAKE_DISTANCE = 2.5;

	public Mimic(EntityType<? extends Mimic> type, Level level) {
		super(type, level);
		this.xpReward = 15;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
			.add(Attributes.MAX_HEALTH, 40.0).add(Attributes.ATTACK_DAMAGE, 8.0).add(Attributes.MOVEMENT_SPEED, 0.32)
			.add(Attributes.ARMOR, 8.0).add(Attributes.KNOCKBACK_RESISTANCE, 0.8);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(AWAKE, false);
	}

	public boolean isAwake() {
		return entityData.get(AWAKE);
	}

	@Override
	protected void registerGoals() {
		this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.2, true) {
			@Override
			public boolean canUse() {
				return isAwake() && super.canUse();
			}
		});
		this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
		this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true) {
			@Override
			public boolean canUse() {
				return isAwake() && super.canUse();
			}
		});
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (!isAwake()) {
			// спящий мимик неподвижен и смотрит строго по сторонам света, как сундук
			setYRot(Math.round(getYRot() / 90.0F) * 90.0F);
			yBodyRot = yHeadRot = getYRot();
			Player near = level.getNearestPlayer(this, WAKE_DISTANCE);
			if (near != null && !near.isCreative() && !near.isSpectator()) {
				wake(near);
			}
		}
	}

	private void wake(LivingEntity target) {
		entityData.set(AWAKE, true);
		setTarget(target);
		playSound(SoundEvents.CHEST_OPEN, 1.0F, 0.6F);
		playSound(SoundEvents.RAVAGER_ROAR, 0.6F, 1.6F);
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (!isAwake() && source.getEntity() instanceof LivingEntity attacker) {
			wake(attacker);
		}
		return super.hurtServer(level, source, amount);
	}

	@Override
	public boolean removeWhenFarAway(double distSqr) {
		return false;
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putBoolean("Awake", isAwake());
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		entityData.set(AWAKE, input.getBooleanOr("Awake", false));
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return isAwake() ? SoundEvents.RAVAGER_AMBIENT : null;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.CHEST_CLOSE;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.WOOD_BREAK;
	}
}
