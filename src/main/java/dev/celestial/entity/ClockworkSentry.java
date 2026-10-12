package dev.celestial.entity;

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
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * Часовой-механоид — страж улиц Хронограда: латунный солдат с алебардой и ключом в спине, ходит строевым шагом.
 * Его завода хватает ненадолго: когда пружина спускается, он встаёт и 3 с заводит себя сам — ключ крутится, броня
 * раскрыта, урон по нему ×1.75. Ждать этого окна — главный приём против часового.
 */
public class ClockworkSentry extends Monster {
	private static final EntityDataAccessor<Integer> REWIND = SynchedEntityData.defineId(ClockworkSentry.class, EntityDataSerializers.INT);
	public static final int REWIND_TICKS = 60;
	private static final byte EVENT_SWING = 4;
	private int attackAnim;
	private int wind = 300;

	public ClockworkSentry(EntityType<? extends ClockworkSentry> type, Level level) {
		super(type, level);
		this.xpReward = 12;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
			.add(Attributes.MAX_HEALTH, 44.0)
			.add(Attributes.ARMOR, 10.0)
			.add(Attributes.MOVEMENT_SPEED, 0.24)
			.add(Attributes.ATTACK_DAMAGE, 8.0)
			.add(Attributes.KNOCKBACK_RESISTANCE, 0.6)
			.add(Attributes.FOLLOW_RANGE, 24.0);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(REWIND, 0);
	}

	@Override
	protected void registerGoals() {
		goalSelector.addGoal(0, new FloatGoal(this));
		goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.1, true));
		goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.7));
		goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 12.0F));
		goalSelector.addGoal(8, new RandomLookAroundGoal(this));
		targetSelector.addGoal(1, new HurtByTargetGoal(this));
		targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
	}

	/** Сколько тиков ещё заводится (0 — на ходу). */
	public int rewinding() {
		return entityData.get(REWIND);
	}

	public float attackProgress(float partial) {
		return attackAnim > 0 ? (attackAnim - partial) / 10.0F : 0.0F;
	}

	@Override
	public boolean isImmobile() {
		return super.isImmobile() || rewinding() > 0;
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (attackAnim > 0) {
			attackAnim--;
		}
		if (level().isClientSide() && rewinding() > 0 && random.nextInt(3) == 0) {
			level().addParticle(ParticleTypes.SMOKE, getX(), getY(1.0) - 0.4, getZ(), 0, 0.05, 0);
		}
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		int r = rewinding();
		if (r > 0) {
			getNavigation().stop();
			entityData.set(REWIND, r - 1);
			if (r % 10 == 0) {
				playSound(dev.celestial.registry.ModSounds.CLOCK_TICK, 0.8F, 0.6F + (REWIND_TICKS - r) * 0.01F);
			}
			if (r == 1) {
				wind = 240 + random.nextInt(160);
				playSound(SoundEvents.CROSSBOW_LOADING_END.value(), 1.0F, 0.8F);
			}
			return;
		}
		// пружина спускается вдвое быстрее в бою
		wind -= getTarget() != null ? 2 : (getDeltaMovement().horizontalDistanceSqr() > 1.0E-4 ? 1 : 0);
		if (wind <= 0) {
			entityData.set(REWIND, REWIND_TICKS);
			playSound(dev.celestial.registry.ModSounds.SENTRY_WIND, 1.0F, 1.0F);
		}
	}

	@Override
	public boolean doHurtTarget(ServerLevel level, Entity target) {
		if (rewinding() > 0) {
			return false;
		}
		attackAnim = 10;
		level.broadcastEntityEvent(this, EVENT_SWING);
		return super.doHurtTarget(level, target);
	}

	@Override
	public void handleEntityEvent(byte id) {
		if (id == EVENT_SWING) {
			attackAnim = 10;
		} else {
			super.handleEntityEvent(id);
		}
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (rewinding() > 0) {
			amount *= 1.75F;
			level.sendParticles(ParticleTypes.CRIT, getX(), getY(0.6), getZ(), 8, 0.3, 0.4, 0.3, 0.2);
		}
		return super.hurtServer(level, source, amount);
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putInt("Wind", wind);
		output.putInt("Rewind", rewinding());
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		wind = input.getIntOr("Wind", 300);
		entityData.set(REWIND, input.getIntOr("Rewind", 0));
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return dev.celestial.registry.ModSounds.CLOCK_TICK;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.IRON_GOLEM_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.IRON_GOLEM_DEATH;
	}

	@Override
	protected void playStepSound(BlockPos pos, BlockState state) {
		playSound(SoundEvents.NETHERITE_BLOCK_STEP, 0.7F, 1.4F);
	}

	@Override
	public float getVoicePitch() {
		return 1.3F;
	}
}
