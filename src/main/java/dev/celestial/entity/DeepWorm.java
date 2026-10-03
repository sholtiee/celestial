package dev.celestial.entity;

import dev.celestial.registry.ModSounds;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * Глубинный червь — мини-босс Бездны. Почти всё время под землёй (неуязвим, выдают его только пыль и грохот),
 * подкрадывается под цель, вырывается с укусом и снова уходит в камень. Бить можно, пока он над землёй.
 * Фазы: BURROW → RISE (вырывается вверх) → EXPOSED (над землёй, кусает) → DIVE (уходит вниз).
 */
public class DeepWorm extends Monster {
	public enum Phase { BURROW, RISE, EXPOSED, DIVE }

	private static final EntityDataAccessor<Integer> PHASE = SynchedEntityData.defineId(DeepWorm.class, EntityDataSerializers.INT);
	private final ServerBossEvent bossEvent = new ServerBossEvent(java.util.UUID.randomUUID(), Component.translatable("entity.celestial.deep_worm"),
		BossEvent.BossBarColor.PURPLE, BossEvent.BossBarOverlay.NOTCHED_6);
	private int phaseTicks;

	public DeepWorm(EntityType<? extends DeepWorm> type, Level level) {
		super(type, level);
		this.xpReward = 60;
		this.noPhysics = true;
		setNoGravity(true);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
			.add(Attributes.MAX_HEALTH, 140.0)
			.add(Attributes.ATTACK_DAMAGE, 12.0)
			.add(Attributes.MOVEMENT_SPEED, 0.25)
			.add(Attributes.FOLLOW_RANGE, 40.0)
			.add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
			.add(Attributes.ARMOR, 8.0);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(PHASE, Phase.BURROW.ordinal());
	}

	public Phase phase() {
		return Phase.values()[entityData.get(PHASE)];
	}

	private void setPhase(Phase phase) {
		entityData.set(PHASE, phase.ordinal());
		phaseTicks = 0;
	}

	@Override
	protected void registerGoals() {
		this.targetSelector.addGoal(1, new NearestAttackableTargetGoal<>(this, Player.class, false));
	}

	@Override
	public void tick() {
		this.noPhysics = true;
		setNoGravity(true);
		super.tick();
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		bossEvent.setProgress(getHealth() / getMaxHealth());
		phaseTicks++;
		LivingEntity target = getTarget();
		// ванильный поиск цели смотрит лишь на ±4 блока по высоте, а червь сидит глубже — ищем сами
		if ((target == null || !target.isAlive() || distanceToSqr(target) > 48 * 48) && tickCount % 10 == 0) {
			Player nearest = level.getNearestPlayer(getX(), getY(), getZ(), 40.0,
				p -> p instanceof Player pl && !pl.isCreative() && !pl.isSpectator());
			setTarget(nearest);
			target = nearest;
		}
		switch (phase()) {
			case BURROW -> burrow(level, target);
			case RISE -> {
				setDeltaMovement(0, 0.55, 0);
				if (phaseTicks == 1) {
					level.playSound(null, blockPosition(), SoundEvents.WARDEN_EMERGE, SoundSource.HOSTILE, 2.0F, 0.7F);
				}
				dust(level, 12);
				if (phaseTicks >= 9) {
					setPhase(Phase.EXPOSED);
					bite(level);
				}
			}
			case EXPOSED -> {
				setDeltaMovement(Vec3.ZERO);
				if (target != null) {
					getLookControl().setLookAt(target, 30, 30);
				}
				if (phaseTicks % 25 == 0) {
					bite(level);
				}
				if (phaseTicks >= 70) {
					setPhase(Phase.DIVE);
				}
			}
			case DIVE -> {
				setDeltaMovement(0, -0.5, 0);
				dust(level, 8);
				if (phaseTicks >= 14) {
					setPhase(Phase.BURROW);
				}
			}
		}
	}

	/** Под землёй: плывёт сквозь камень к точке под целью, подняв пыль на поверхности. */
	private void burrow(ServerLevel level, LivingEntity target) {
		setInvisible(true);
		if (target == null) {
			setDeltaMovement(getDeltaMovement().scale(0.8));
			return;
		}
		Vec3 below = target.position().add(0, -5, 0);
		Vec3 delta = below.subtract(position());
		setDeltaMovement(delta.length() > 0.5 ? delta.normalize().scale(0.35) : Vec3.ZERO);
		if (tickCount % 6 == 0) {
			BlockPos ground = BlockPos.containing(getX(), target.getY() - 1, getZ());
			BlockState state = level.getBlockState(ground);
			if (!state.isAir()) {
				level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state), getX(), target.getY() + 0.1, getZ(), 10, 0.6, 0.1, 0.6, 0.05);
			}
			if (tickCount % 30 == 0) {
				level.playSound(null, ground, SoundEvents.GRAVEL_BREAK, SoundSource.HOSTILE, 1.5F, 0.4F);
			}
		}
		if (phaseTicks > 60 && delta.horizontalDistanceSqr() < 2.5) {
			setInvisible(false);
			setPhase(Phase.RISE);
		}
	}

	private void bite(ServerLevel level) {
		playSound(ModSounds.WORM_BITE, 2.0F, 0.8F);
		for (ServerPlayer p : level.getEntitiesOfClass(ServerPlayer.class, getBoundingBox().inflate(2.5, 1.5, 2.5))) {
			p.hurtServer(level, damageSources().mobAttack(this), (float) getAttributeValue(Attributes.ATTACK_DAMAGE));
			p.setDeltaMovement(p.position().subtract(position()).normalize().scale(0.8).add(0, 0.6, 0));
			p.needsSync = true;
		}
	}

	private void dust(ServerLevel level, int count) {
		BlockPos at = blockPosition().above(2);
		BlockState state = level.getBlockState(at.below(3));
		if (!state.isAir()) {
			level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state), getX(), getY() + 2, getZ(), count, 0.8, 0.5, 0.8, 0.1);
		}
	}

	/** Под землёй червь неуязвим (кроме /kill), а удушье в камне ему вообще не страшно. */
	@Override
	public boolean isInvulnerableTo(ServerLevel level, DamageSource source) {
		if (source.is(net.minecraft.world.damagesource.DamageTypes.IN_WALL)) {
			return true;
		}
		if ((phase() == Phase.BURROW || phase() == Phase.DIVE && phaseTicks > 6) && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
			return true;
		}
		return super.isInvulnerableTo(level, source);
	}

	@Override
	public boolean isPushable() {
		return false;
	}

	@Override
	public boolean causeFallDamage(double fallDistance, float multiplier, DamageSource source) {
		return false;
	}

	@Override
	public void startSeenByPlayer(ServerPlayer player) {
		super.startSeenByPlayer(player);
		bossEvent.addPlayer(player);
	}

	@Override
	public void stopSeenByPlayer(ServerPlayer player) {
		super.stopSeenByPlayer(player);
		bossEvent.removePlayer(player);
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putInt("WormPhase", phase().ordinal());
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		setPhase(Phase.values()[Math.floorMod(input.getIntOr("WormPhase", 0), Phase.values().length)]);
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.RAVAGER_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.RAVAGER_DEATH;
	}

	@Override
	public float getVoicePitch() {
		return 0.6F;
	}
}
