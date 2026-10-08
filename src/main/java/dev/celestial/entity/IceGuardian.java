package dev.celestial.entity;

import dev.celestial.data.CelestialData;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
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
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * Ледяной страж — голем из вечного льда, хранитель цитадели Архонта. Медленный и тяжёлый: размашистый удар замедляет,
 * «сотрясение» бьёт всех рядом и вытягивает тепло, а «ледяной щит» (видимые на модели пластины) на 3 с режет урон втрое.
 * Огонь ранит его сильнее, мороз не берёт.
 */
public class IceGuardian extends Monster {
	private static final EntityDataAccessor<Boolean> SHIELD = SynchedEntityData.defineId(IceGuardian.class, EntityDataSerializers.BOOLEAN);
	private static final byte EVENT_SWING = 4;
	private static final byte EVENT_SLAM = 60;
	private int attackAnim;
	private int slamAnim;
	private int shieldTicks;
	private int shieldCooldown = 100;
	private int slamCooldown = 80;

	public IceGuardian(EntityType<? extends IceGuardian> type, Level level) {
		super(type, level);
		this.xpReward = 20;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
			.add(Attributes.MAX_HEALTH, 80.0)
			.add(Attributes.ARMOR, 8.0)
			.add(Attributes.MOVEMENT_SPEED, 0.22)
			.add(Attributes.ATTACK_DAMAGE, 11.0)
			.add(Attributes.ATTACK_KNOCKBACK, 1.2)
			.add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
			.add(Attributes.FOLLOW_RANGE, 24.0)
			.add(Attributes.STEP_HEIGHT, 1.0);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(SHIELD, false);
	}

	@Override
	protected void registerGoals() {
		goalSelector.addGoal(0, new FloatGoal(this));
		goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.0, true));
		goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.6));
		goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 10.0F));
		goalSelector.addGoal(8, new RandomLookAroundGoal(this));
		targetSelector.addGoal(1, new HurtByTargetGoal(this));
		targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
	}

	public boolean shielded() {
		return entityData.get(SHIELD);
	}

	public float attackProgress(float partial) {
		return attackAnim > 0 ? (attackAnim - partial) / 10.0F : 0.0F;
	}

	public float slamProgress(float partial) {
		return slamAnim > 0 ? (slamAnim - partial) / 16.0F : 0.0F;
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (attackAnim > 0) {
			attackAnim--;
		}
		if (slamAnim > 0) {
			slamAnim--;
		}
		if (level().isClientSide()) {
			if (random.nextInt(shielded() ? 1 : 4) == 0) {
				level().addParticle(ParticleTypes.SNOWFLAKE, getRandomX(0.7), getRandomY(), getRandomZ(0.7), 0, -0.03, 0);
			}
		}
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (shieldTicks > 0 && --shieldTicks == 0) {
			entityData.set(SHIELD, false);
		}
		if (shieldCooldown > 0) {
			shieldCooldown--;
		}
		if (slamCooldown > 0) {
			slamCooldown--;
		}
		LivingEntity target = getTarget();
		if (target != null && slamCooldown == 0 && onGround() && distanceToSqr(target) < 16) {
			slam(level);
		}
	}

	/** Сотрясение: удар обеими руками в лёд — урон, отброс и холод всем в радиусе 4. */
	private void slam(ServerLevel level) {
		slamCooldown = 140 + random.nextInt(60);
		level.broadcastEntityEvent(this, EVENT_SLAM);
		slamAnim = 16;
		level.playSound(null, blockPosition(), dev.celestial.registry.ModSounds.ICE_CRACK, SoundSource.HOSTILE, 2.0F, 0.6F);
		level.playSound(null, blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 0.6F, 1.6F);
		for (int i = 0; i < 40; i++) {
			double a = i / 40.0 * Math.PI * 2;
			level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState()),
				getX() + Math.cos(a) * 3, getY() + 0.1, getZ() + Math.sin(a) * 3, 2, 0.2, 0.1, 0.2, 0.15);
		}
		level.sendParticles(ParticleTypes.SNOWFLAKE, getX(), getY() + 0.5, getZ(), 60, 2.0, 0.3, 2.0, 0.1);
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(4.0, 1.0, 4.0),
			e -> e != this && !(e instanceof IceGuardian) && e.isAlive())) {
			if (e instanceof Player p && (p.isCreative() || p.isSpectator())) {
				continue;
			}
			e.hurtServer(level, damageSources().mobAttack(this), 7.0F);
			Vec3 push = e.position().subtract(position()).multiply(1, 0, 1).normalize().scale(1.1);
			e.push(push.x, 0.45, push.z);
			e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 2), this);
			if (e instanceof ServerPlayer sp) {
				sp.needsSync = true;
				CelestialData.update(sp, d -> d.withWarmth(d.warmth() - 10));
			}
		}
	}

	@Override
	public boolean doHurtTarget(ServerLevel level, Entity target) {
		attackAnim = 10;
		level.broadcastEntityEvent(this, EVENT_SWING);
		boolean hit = super.doHurtTarget(level, target);
		if (hit && target instanceof LivingEntity living) {
			living.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1), this);
			living.setTicksFrozen(Math.min(living.getTicksRequiredToFreeze(), living.getTicksFrozen() + 60));
			playSound(SoundEvents.GLASS_HIT, 1.2F, 0.5F);
		}
		return hit;
	}

	@Override
	public void handleEntityEvent(byte id) {
		if (id == EVENT_SWING) {
			attackAnim = 10;
		} else if (id == EVENT_SLAM) {
			slamAnim = 16;
		} else {
			super.handleEntityEvent(id);
		}
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (source.is(DamageTypeTags.IS_FREEZING)) {
			return false;
		}
		if (source.is(DamageTypeTags.IS_FIRE)) {
			amount *= 1.6F;
		}
		if (shielded()) {
			amount *= 0.3F;
			level.sendParticles(ParticleTypes.SNOWFLAKE, getX(), getY(1.0), getZ(), 10, 0.6, 0.6, 0.6, 0.05);
			playSound(SoundEvents.AMETHYST_BLOCK_HIT, 1.0F, 0.6F);
		} else if (shieldCooldown == 0 && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY) && random.nextInt(3) == 0) {
			// поднимает щит в ответ на удар
			shieldCooldown = 200;
			shieldTicks = 60;
			entityData.set(SHIELD, true);
			playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 1.5F, 0.5F);
		}
		return super.hurtServer(level, source, amount);
	}

	@Override
	public boolean canFreeze() {
		return false;
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putInt("ShieldTicks", shieldTicks);
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		shieldTicks = input.getIntOr("ShieldTicks", 0);
		entityData.set(SHIELD, shieldTicks > 0);
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return SoundEvents.AMETHYST_BLOCK_CHIME;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return dev.celestial.registry.ModSounds.GUARDIAN_CRACK;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.GLASS_BREAK;
	}

	@Override
	protected void playStepSound(BlockPos pos, net.minecraft.world.level.block.state.BlockState state) {
		playSound(SoundEvents.IRON_GOLEM_STEP, 0.8F, 0.6F);
	}

	@Override
	public float getVoicePitch() {
		return 0.6F;
	}
}
