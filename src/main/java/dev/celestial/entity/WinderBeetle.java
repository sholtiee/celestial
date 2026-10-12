package dev.celestial.entity;

import dev.celestial.chrono.PendulumBlock;
import dev.celestial.chrono.PendulumBlockEntity;
import dev.celestial.chrono.TimeFlow;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LeapAtTargetGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * Жук-заводняк — латунный жук с ключиком на спине, ходит роем. Рядом с качающимся маятником (или в зоне ускоренного
 * времени) «подзаводится»: 10 с бегает вдвое резвее и кусает сильнее, ключ на спине крутится, глаза горят ярче.
 * Остановить маятник Камертоном — лучший способ успокоить рой. Его же призывает Часовщик во второй фазе.
 */
public class WinderBeetle extends Monster {
	private static final EntityDataAccessor<Integer> WOUND = SynchedEntityData.defineId(WinderBeetle.class, EntityDataSerializers.INT);
	public static final int WOUND_TICKS = 200;
	public static final int PENDULUM_RADIUS = 6;

	public WinderBeetle(EntityType<? extends WinderBeetle> type, Level level) {
		super(type, level);
		this.xpReward = 3;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
			.add(Attributes.MAX_HEALTH, 10.0)
			.add(Attributes.ARMOR, 4.0)
			.add(Attributes.MOVEMENT_SPEED, 0.3)
			.add(Attributes.ATTACK_DAMAGE, 3.0)
			.add(Attributes.FOLLOW_RANGE, 20.0);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(WOUND, 0);
	}

	@Override
	protected void registerGoals() {
		goalSelector.addGoal(0, new FloatGoal(this));
		goalSelector.addGoal(2, new LeapAtTargetGoal(this, 0.35F));
		goalSelector.addGoal(3, new MeleeAttackGoal(this, 1.15, false));
		goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8));
		goalSelector.addGoal(8, new RandomLookAroundGoal(this));
		targetSelector.addGoal(1, new HurtByTargetGoal(this, WinderBeetle.class).setAlertOthers());
		targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
	}

	public boolean wound() {
		return entityData.get(WOUND) > 0;
	}

	/** Подзавести на {@code ticks} (Часовщик подзаводит призванных сразу). */
	public void windUp(int ticks) {
		if (!wound()) {
			playSound(dev.celestial.registry.ModSounds.SENTRY_WIND, 0.5F, 1.8F);
		}
		entityData.set(WOUND, Math.max(entityData.get(WOUND), ticks));
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (level().isClientSide() && wound() && random.nextInt(4) == 0) {
			level().addParticle(dev.celestial.registry.ModParticles.CHRONO_HASTE, getRandomX(0.5), getY() + 0.4, getRandomZ(0.5), 0, 0.02, 0);
		}
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		int w = entityData.get(WOUND);
		if (w > 0) {
			entityData.set(WOUND, w - 1);
			addEffect(new MobEffectInstance(MobEffects.SPEED, 5, 1, false, false));
			addEffect(new MobEffectInstance(MobEffects.STRENGTH, 5, 0, false, false));
		}
		if ((tickCount + getId()) % 20 == 0 && (TimeFlow.scale(this) != 1.0F || nearSwingingPendulum(level))) {
			windUp(WOUND_TICKS);
		}
	}

	/** Качающийся маятник в радиусе 6 — ищем по сущностям блоков соседних чанков, а не перебором блоков. */
	private boolean nearSwingingPendulum(ServerLevel level) {
		BlockPos at = blockPosition();
		int r2 = PENDULUM_RADIUS * PENDULUM_RADIUS;
		ChunkPos min = ChunkPos.containing(at.offset(-PENDULUM_RADIUS, 0, -PENDULUM_RADIUS));
		ChunkPos max = ChunkPos.containing(at.offset(PENDULUM_RADIUS, 0, PENDULUM_RADIUS));
		for (int cx = min.x(); cx <= max.x(); cx++) {
			for (int cz = min.z(); cz <= max.z(); cz++) {
				if (!level.hasChunk(cx, cz)) {
					continue;
				}
				for (BlockEntity be : level.getChunk(cx, cz).getBlockEntities().values()) {
					if (be instanceof PendulumBlockEntity && be.getBlockPos().distSqr(at) <= r2) {
						BlockState state = be.getBlockState();
						if (state.getBlock() instanceof PendulumBlock && state.getValue(PendulumBlock.SWINGING)) {
							return true;
						}
					}
				}
			}
		}
		return false;
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		boolean hurt = super.hurtServer(level, source, amount);
		if (hurt) {
			level.sendParticles(ParticleTypes.SMALL_FLAME, getX(), getY(0.5), getZ(), 3, 0.2, 0.1, 0.2, 0.02);
		}
		return hurt;
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putInt("Wound", entityData.get(WOUND));
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		entityData.set(WOUND, input.getIntOr("Wound", 0));
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return dev.celestial.registry.ModSounds.BEETLE_CHITTER;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.CHAIN_HIT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.SILVERFISH_DEATH;
	}

	@Override
	protected void playStepSound(BlockPos pos, BlockState state) {
		playSound(SoundEvents.SILVERFISH_STEP, 0.15F, 1.6F);
	}

	@Override
	public float getVoicePitch() {
		return 1.5F;
	}
}
