package dev.celestial.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * Офаним — «колёса, полные очей» (Иез. 1:15–21): два вложенных кольца с глазами вокруг огромного ока, парят над Долиной часов.
 * Держатся поодаль и смотрят: каждые ~5 с наводят луч (видна нить света к цели, 2,5 с), и если цель не ушла из-под
 * взгляда за укрытие — луч бьёт и замедляет. Время их не берёт (тег time_immune), огонь тоже.
 */
public class Ophanim extends Mob implements Enemy {
	private static final EntityDataAccessor<Integer> BEAM_TARGET = SynchedEntityData.defineId(Ophanim.class, EntityDataSerializers.INT);
	private static final EntityDataAccessor<Integer> BEAM_CHARGE = SynchedEntityData.defineId(Ophanim.class, EntityDataSerializers.INT);
	public static final int CHARGE_TICKS = 50;
	private int beamCooldown = 60;

	public Ophanim(EntityType<? extends Ophanim> type, Level level) {
		super(type, level);
		this.moveControl = new FlyingMoveControl<>(this, 10, true);
		this.xpReward = 18;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes()
			.add(Attributes.MAX_HEALTH, 50.0)
			.add(Attributes.ARMOR, 4.0)
			.add(Attributes.FLYING_SPEED, 0.35)
			.add(Attributes.MOVEMENT_SPEED, 0.2)
			.add(Attributes.ATTACK_DAMAGE, 9.0)
			.add(Attributes.FOLLOW_RANGE, 28.0);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(BEAM_TARGET, -1);
		builder.define(BEAM_CHARGE, 0);
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

	/** Насколько заряжен луч, 0..1 (0 — луча нет). */
	public float beamProgress(float partial) {
		int c = entityData.get(BEAM_CHARGE);
		return c > 0 ? Math.min(1.0F, (c + partial) / CHARGE_TICKS) : 0.0F;
	}

	public Entity beamTarget() {
		int id = entityData.get(BEAM_TARGET);
		return id < 0 ? null : level().getEntity(id);
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (beamCooldown > 0) {
			beamCooldown--;
		}
		ServerPlayer target = (ServerPlayer) level.getNearestPlayer(getX(), getY(), getZ(), getAttributeValue(Attributes.FOLLOW_RANGE),
			p -> p instanceof ServerPlayer sp && !sp.isCreative() && !sp.isSpectator());
		if (target == null) {
			cancelBeam();
			if (getNavigation().isDone() && random.nextInt(80) == 0) {
				Vec3 p = position().add((random.nextDouble() - 0.5) * 14, (random.nextDouble() - 0.45) * 4, (random.nextDouble() - 0.5) * 14);
				getNavigation().moveTo(p.x, p.y, p.z, 0.5);
			}
			return;
		}
		getLookControl().setLookAt(target, 30.0F, 30.0F);
		// кружит в 7–9 блоках, на 3–4 выше цели
		if (tickCount % 20 == 0 || getNavigation().isDone()) {
			double a = Math.atan2(getZ() - target.getZ(), getX() - target.getX()) + 0.35;
			double r = 7.5 + random.nextDouble() * 1.5;
			getNavigation().moveTo(target.getX() + Math.cos(a) * r, target.getY() + 3.5, target.getZ() + Math.sin(a) * r, 0.7);
		}
		int charge = entityData.get(BEAM_CHARGE);
		if (charge == 0) {
			if (beamCooldown == 0 && hasLineOfSight(target)) {
				entityData.set(BEAM_TARGET, target.getId());
				entityData.set(BEAM_CHARGE, 1);
				level.playSound(null, blockPosition(), dev.celestial.registry.ModSounds.OPHANIM_CHARGE, SoundSource.HOSTILE, 1.4F, 1.0F);
			}
			return;
		}
		Entity aimed = beamTarget();
		if (!(aimed instanceof LivingEntity living) || !living.isAlive() || distanceToSqr(living) > 40 * 40) {
			cancelBeam();
			return;
		}
		if (charge < CHARGE_TICKS) {
			entityData.set(BEAM_CHARGE, charge + 1);
			return;
		}
		// разряд: попадает, только если цель всё ещё на виду
		if (hasLineOfSight(living)) {
			living.hurtServer(level, damageSources().indirectMagic(this, this), (float) getAttributeValue(Attributes.ATTACK_DAMAGE));
			living.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 1), this);
			Vec3 from = position().add(0, getBbHeight() / 2, 0);
			Vec3 to = living.getEyePosition().subtract(0, 0.3, 0);
			for (int i = 0; i <= 16; i++) {
				Vec3 p = from.lerp(to, i / 16.0);
				level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 1, 0.02, 0.02, 0.02, 0.0);
			}
			level.sendParticles(ParticleTypes.ELECTRIC_SPARK, to.x, to.y, to.z, 12, 0.3, 0.3, 0.3, 0.2);
			level.playSound(null, living.blockPosition(), dev.celestial.registry.ModSounds.OPHANIM_BEAM, SoundSource.HOSTILE, 1.5F, 1.0F);
		} else {
			level.playSound(null, blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 0.8F, 1.6F);
		}
		cancelBeam();
	}

	private void cancelBeam() {
		if (entityData.get(BEAM_CHARGE) != 0) {
			entityData.set(BEAM_CHARGE, 0);
			entityData.set(BEAM_TARGET, -1);
			beamCooldown = 60 + random.nextInt(40);
		}
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (!level().isClientSide()) {
			return;
		}
		if (random.nextInt(4) == 0) {
			level().addParticle(ParticleTypes.END_ROD, getRandomX(0.9), getRandomY(), getRandomZ(0.9), 0, 0.01, 0);
		}
		// нить наведения: пунктир от ока к цели, к концу заряда — всё гуще
		Entity aimed = beamTarget();
		float p = beamProgress(0);
		if (aimed != null && p > 0) {
			Vec3 from = position().add(0, getBbHeight() / 2, 0);
			Vec3 to = aimed.getEyePosition().subtract(0, 0.3, 0);
			int n = 4 + (int) (p * 10);
			for (int i = 0; i < n; i++) {
				Vec3 q = from.lerp(to, random.nextDouble());
				level().addParticle(p > 0.8F ? ParticleTypes.ELECTRIC_SPARK : ParticleTypes.WAX_ON, q.x, q.y, q.z, 0, 0, 0);
			}
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
		return dev.celestial.registry.ModSounds.OPHANIM_HUM;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.AMETHYST_CLUSTER_HIT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.BEACON_DEACTIVATE;
	}

	@Override
	public float getVoicePitch() {
		return 0.7F;
	}
}
