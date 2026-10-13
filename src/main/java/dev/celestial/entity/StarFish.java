package dev.celestial.entity;

import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * Звёздная рыба — мирная стайка Астрала: «плывут» в пустоте вслед за вожаком (самой старшей рыбой поблизости),
 * огибая астероиды, и шарахаются от странника. Светятся. С них — звёздная чешуя.
 */
public class StarFish extends PathfinderMob {
	public StarFish(EntityType<? extends StarFish> type, Level level) {
		super(type, level);
		this.moveControl = new FlyingMoveControl<>(this, 20, true);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return PathfinderMob.createMobAttributes()
			.add(Attributes.MAX_HEALTH, 4.0)
			.add(Attributes.FLYING_SPEED, 0.6)
			.add(Attributes.MOVEMENT_SPEED, 0.25)
			.add(Attributes.FOLLOW_RANGE, 16.0);
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
		if (tickCount % 10 != (getId() % 10)) {
			return;
		}
		Player near = level.getNearestPlayer(this, 5.0);
		if (near != null && !near.isSpectator()) {  // шарахается
			Vec3 away = position().subtract(near.position()).normalize().scale(8);
			getNavigation().moveTo(getX() + away.x, getY() + away.y + 1, getZ() + away.z, 1.6);
			return;
		}
		List<StarFish> school = level.getEntitiesOfClass(StarFish.class, getBoundingBox().inflate(12), f -> f != this);
		StarFish leader = school.stream().filter(f -> f.tickCount > tickCount).findFirst().orElse(null);
		if (leader != null) {  // держимся вожака, со сдвигом по id — чтобы не слипаться
			double a = getId() * 1.7;
			getNavigation().moveTo(leader.getX() + Math.cos(a) * 2, leader.getY() + Math.sin(a), leader.getZ() + Math.sin(a) * 2, 1.0);
		} else if (getNavigation().isDone()) {
			Vec3 p = position().add((random.nextDouble() - 0.5) * 20, (random.nextDouble() - 0.5) * 6, (random.nextDouble() - 0.5) * 20);
			getNavigation().moveTo(p.x, p.y, p.z, 0.8);
		}
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (level().isClientSide() && random.nextInt(6) == 0) {
			level().addParticle(ParticleTypes.END_ROD, getX(), getY(0.5), getZ(), 0, 0, 0);
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
	public boolean removeWhenFarAway(double distSqr) {
		return distSqr > 96 * 96;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.TROPICAL_FISH_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.TROPICAL_FISH_DEATH;
	}

	@Override
	public float getVoicePitch() {
		return 1.4F;
	}
}
