package dev.celestial.entity;

import dev.celestial.registry.ModSounds;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Слепой охотник Бездны: глаз нет, охотится на звук. Слышит игрока в радиусе 16, если тот идёт, бежит или прыгает;
 * крадущихся и замерших не замечает. Потеряв цель, идёт проверить место, где слышал её последний раз.
 */
public class BlindHunter extends Monster {
	private static final EntityDataAccessor<Boolean> HUNTING = SynchedEntityData.defineId(BlindHunter.class, EntityDataSerializers.BOOLEAN);
	private static final double HEARING = 16.0;
	private @Nullable Vec3 lastHeard;
	private int listenCooldown;

	public BlindHunter(EntityType<? extends BlindHunter> type, Level level) {
		super(type, level);
		this.xpReward = 15;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
			.add(Attributes.MAX_HEALTH, 60.0)
			.add(Attributes.ATTACK_DAMAGE, 10.0)
			.add(Attributes.MOVEMENT_SPEED, 0.3)
			.add(Attributes.FOLLOW_RANGE, HEARING)
			.add(Attributes.KNOCKBACK_RESISTANCE, 0.6)
			.add(Attributes.STEP_HEIGHT, 1.0);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(HUNTING, false);
	}

	/** Для модели: охотник выпрямляется и тянет руки, когда идёт на звук. */
	public boolean isHunting() {
		return entityData.get(HUNTING);
	}

	@Override
	protected void registerGoals() {
		this.goalSelector.addGoal(0, new FloatGoal(this));
		this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.25, true));
		this.goalSelector.addGoal(8, new WaterAvoidingRandomStrollGoal(this, 0.6));
	}

	/** Шумит ли игрок: ходит не крадучись, бежит или прыгает (стоящих и крадущихся не слышно). */
	public static boolean isNoisy(Player player) {
		if (player.isSpectator() || player.isCreative() || player.isShiftKeyDown()) {
			return false;
		}
		// на сервере скорость игрока почти всегда 0 (он движется на клиенте) — берём то, что прислал клиент
		Vec3 v = player instanceof net.minecraft.server.level.ServerPlayer sp ? sp.getKnownMovement() : player.getDeltaMovement();
		double horizontal = v.x * v.x + v.z * v.z;
		return player.isSprinting() || !player.onGround() && v.y > 0.1 || horizontal > 0.004;
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (listenCooldown > 0) {
			listenCooldown--;
		}
		LivingEntity target = getTarget();
		if (target instanceof Player player && (!player.isAlive() || distanceToSqr(player) > HEARING * HEARING * 1.5
			|| !isNoisy(player) && distanceToSqr(player) > 9)) {
			lastHeard = player.position();
			setTarget(null);
			target = null;
		}
		if (target == null && listenCooldown == 0) {
			listenCooldown = 5;
			Player heard = level.getNearestPlayer(getX(), getY(), getZ(), HEARING, p -> p instanceof Player pl && isNoisy(pl));
			if (heard != null) {
				setTarget(heard);
				target = heard;
				playSound(ModSounds.HUNTER_SCREECH, 1.6F, 0.9F + random.nextFloat() * 0.2F);
			}
		}
		if (target == null && lastHeard != null) {
			getNavigation().moveTo(lastHeard.x, lastHeard.y, lastHeard.z, 1.0);
			if (position().distanceToSqr(lastHeard) < 4) {
				lastHeard = null;
			}
		}
		entityData.set(HUNTING, target != null);
		if (target != null && tickCount % 4 == 0) {
			level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, getX(), getEyeY() + 0.3, getZ(), 2, 0.25, 0.1, 0.25, 0.01);
		}
	}

	@Override
	public boolean doHurtTarget(ServerLevel level, Entity target) {
		boolean hit = super.doHurtTarget(level, target);
		if (hit && target instanceof LivingEntity living) {
			Vec3 push = living.position().subtract(position()).multiply(1, 0, 1).normalize().scale(0.9);
			living.setDeltaMovement(living.getDeltaMovement().add(push.x, 0.35, push.z));
			living.needsSync = true;
		}
		return hit;
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return SoundEvents.WARDEN_SNIFF;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.WARDEN_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.WARDEN_DEATH;
	}

	@Override
	protected void playStepSound(BlockPos pos, net.minecraft.world.level.block.state.BlockState state) {
		playSound(SoundEvents.WARDEN_STEP, 0.6F, 1.2F);
	}

	@Override
	public float getVoicePitch() {
		return 1.3F;
	}
}
