package dev.celestial.entity;

import dev.celestial.data.CelestialData;
import dev.celestial.world.frozen.Cold;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * Морозный дух Ледяных Чертогов: парящий призрак в капюшоне. Подлетает к игроку и вытягивает тепло
 * (−15 за касание, замедление), но боится огня — у костра и жаровни отступает.
 */
public class FrostWraith extends Mob implements Enemy {
	private int touchCooldown;

	public FrostWraith(EntityType<? extends FrostWraith> type, Level level) {
		super(type, level);
		this.moveControl = new FlyingMoveControl<>(this, 20, true);
		this.xpReward = 8;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes()
			.add(Attributes.MAX_HEALTH, 20.0)
			.add(Attributes.FLYING_SPEED, 0.5)
			.add(Attributes.MOVEMENT_SPEED, 0.25)
			.add(Attributes.ATTACK_DAMAGE, 3.0)
			.add(Attributes.FOLLOW_RANGE, 20.0);
	}

	@Override
	protected PathNavigation createNavigation(Level level) {
		FlyingPathNavigation nav = new FlyingPathNavigation(this, level);
		nav.setCanFloat(true);
		return nav;
	}

	@Override
	public void travel(Vec3 input) {
		travelFlying(input, getSpeed());
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (touchCooldown > 0) {
			touchCooldown--;
		}
		ServerPlayer target = (ServerPlayer) level.getNearestPlayer(getX(), getY(), getZ(), 20.0,
			p -> p instanceof ServerPlayer sp && !sp.isCreative() && !sp.isSpectator());
		if (target == null) {
			if (getNavigation().isDone() && random.nextInt(60) == 0) {
				Vec3 p = position().add((random.nextDouble() - 0.5) * 12, (random.nextDouble() - 0.4) * 4, (random.nextDouble() - 0.5) * 12);
				getNavigation().moveTo(p.x, p.y, p.z, 0.6);
			}
			return;
		}
		if (Cold.nearHeat(level, target.blockPosition()) || Cold.nearHeat(level, blockPosition())) {
			// огонь рядом — держится в стороне, кружит на расстоянии
			Vec3 away = position().subtract(target.position()).multiply(1, 0, 1).normalize().scale(8);
			Vec3 p = target.position().add(away).add(0, 3, 0);
			getNavigation().moveTo(p.x, p.y, p.z, 1.0);
			return;
		}
		getNavigation().moveTo(target.getX(), target.getEyeY() - 0.5, target.getZ(), 1.1);
		getLookControl().setLookAt(target);
		if (distanceToSqr(target) < 6 && touchCooldown == 0) {
			touchCooldown = 30;
			CelestialData.update(target, d -> d.withWarmth(d.warmth() - 15));
			target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1), this);
			target.hurtServer(level, damageSources().mobAttack(this), (float) getAttributeValue(Attributes.ATTACK_DAMAGE));
			level.sendParticles(ParticleTypes.SNOWFLAKE, target.getX(), target.getEyeY(), target.getZ(), 25, 0.4, 0.4, 0.4, 0.05);
			playSound(SoundEvents.POWDER_SNOW_STEP, 1.2F, 0.6F);
		}
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (level().isClientSide() && random.nextInt(3) == 0) {
			level().addParticle(ParticleTypes.SNOWFLAKE, getRandomX(0.5), getRandomY(), getRandomZ(0.5), 0, -0.02, 0);
		}
	}

	@Override
	public boolean causeFallDamage(double fallDistance, float multiplier, DamageSource source) {
		return false;
	}

	@Override
	protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return SoundEvents.VEX_AMBIENT;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.VEX_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.VEX_DEATH;
	}

	@Override
	public float getVoicePitch() {
		return 0.6F;
	}
}
