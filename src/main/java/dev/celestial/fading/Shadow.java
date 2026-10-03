package dev.celestial.fading;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * Тень — порождение Угасания. Приходит ночью в Верхний мир, горит на солнце, боится света.
 * Удар насылает Тьму; иногда Тень «перетекает» за спину жертве.
 */
public class Shadow extends Monster {
	private int blinkCooldown = 80;

	public Shadow(EntityType<? extends Shadow> type, Level level) {
		super(type, level);
		this.xpReward = 7;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
			.add(Attributes.MAX_HEALTH, 24.0)
			.add(Attributes.ATTACK_DAMAGE, 5.0)
			.add(Attributes.MOVEMENT_SPEED, 0.28)
			.add(Attributes.FOLLOW_RANGE, 40.0);
	}

	@Override
	protected void registerGoals() {
		this.goalSelector.addGoal(0, new FloatGoal(this));
		this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.15, false));
		this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8));
		this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 12.0F));
		this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
		this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
		this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
		this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, AbstractVillager.class, false));
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (level().isClientSide()) {
			if (random.nextInt(3) == 0) {
				level().addParticle(dev.celestial.registry.ModParticles.SHADOW, getRandomX(0.6), getRandomY(), getRandomZ(0.6), 0, 0.02, 0);
			}
			return;
		}
		if (blinkCooldown > 0) {
			blinkCooldown--;
		}
		LivingEntity target = getTarget();
		if (target != null && blinkCooldown == 0 && distanceToSqr(target) > 16 && distanceToSqr(target) < 400 && random.nextInt(20) == 0) {
			blinkBehind(target);
		}
	}

	/** Перетекает за спину цели. */
	private void blinkBehind(LivingEntity target) {
		Vec3 back = target.getLookAngle().multiply(1, 0, 1).normalize().scale(-2.5);
		Vec3 to = target.position().add(back);
		ServerLevel level = (ServerLevel) level();
		level.sendParticles(dev.celestial.registry.ModParticles.SHADOW, getX(), getY(1), getZ(), 25, 0.3, 0.6, 0.3, 0.02);
		if (randomTeleport(to.x, to.y, to.z, false, state -> false)) {
			level.sendParticles(dev.celestial.registry.ModParticles.SHADOW, getX(), getY(1), getZ(), 25, 0.3, 0.6, 0.3, 0.02);
			playSound(dev.celestial.registry.ModSounds.SHADOW_BLINK, 0.8F, 1.0F);
		}
		blinkCooldown = 120;
	}

	@Override
	public boolean doHurtTarget(ServerLevel level, Entity target) {
		boolean hit = super.doHurtTarget(level, target);
		if (hit && target instanceof LivingEntity living) {
			living.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 80), this);
		}
		return hit;
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return dev.celestial.registry.ModSounds.SHADOW_AMBIENT;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.PHANTOM_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.PHANTOM_DEATH;
	}

	@Override
	public float getVoicePitch() {
		return 0.5F;
	}
}
