package dev.celestial.entity;

import java.util.ArrayDeque;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
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
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * Кукла-латунь — заводная кукла мастеров Хронограда. Своей воли у неё нет: она повторяет движения того, на кого смотрит,
 * с задержкой в полторы секунды — идёт по его следам, прыгает там, где прыгнул он, поворачивает голову, как он, и бьёт,
 * если он замахнулся. Стоишь — стоит и она (лишь подбирается по уже пройденному пути). Уводи её в ловушку собственным маршрутом.
 */
public class BrassDoll extends Monster {
	public static final int DELAY = 30;
	private static final byte EVENT_SWING = 4;
	private final ArrayDeque<Echo> echoes = new ArrayDeque<>();
	private int attackAnim;
	private int attackCooldown;
	private boolean targetWasSwinging;

	/** Снимок движения цели: где стоял, куда смотрел, замахивался ли. */
	private record Echo(Vec3 pos, float yRot, float xRot, boolean swing) {}

	public BrassDoll(EntityType<? extends BrassDoll> type, Level level) {
		super(type, level);
		this.xpReward = 10;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
			.add(Attributes.MAX_HEALTH, 26.0)
			.add(Attributes.ARMOR, 6.0)
			.add(Attributes.MOVEMENT_SPEED, 0.32)
			.add(Attributes.ATTACK_DAMAGE, 6.0)
			.add(Attributes.FOLLOW_RANGE, 24.0);
	}

	@Override
	protected void registerGoals() {
		goalSelector.addGoal(0, new FloatGoal(this));
		targetSelector.addGoal(1, new HurtByTargetGoal(this));
		targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
	}

	public float attackProgress(float partial) {
		return attackAnim > 0 ? (attackAnim - partial) / 8.0F : 0.0F;
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (attackAnim > 0) {
			attackAnim--;
		}
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (attackCooldown > 0) {
			attackCooldown--;
		}
		LivingEntity target = getTarget();
		if (target == null || !target.isAlive() || distanceToSqr(target) > 32 * 32) {
			echoes.clear();
			getNavigation().stop();
			return;
		}
		boolean swingStart = target.isSwinging() && !targetWasSwinging;  // начало замаха цели
		targetWasSwinging = target.isSwinging();
		echoes.addLast(new Echo(target.position(), target.getYHeadRot(), target.getXRot(), swingStart));
		if (echoes.size() <= DELAY) {
			return;  // ещё «запоминает»
		}
		Echo e = echoes.pollFirst();
		// идёт туда, где цель была полторы секунды назад, и смотрит так же
		if (e.pos.distanceToSqr(position()) > 0.09) {
			if (tickCount % 4 == 0 || getNavigation().isDone()) {
				getNavigation().moveTo(e.pos.x, e.pos.y, e.pos.z, 1.2);
			}
			if (e.pos.y > getY() + 0.6 && onGround()) {
				getJumpControl().jump();
			}
		} else {
			getNavigation().stop();
		}
		setYHeadRot(e.yRot);
		setXRot(e.xRot);
		boolean close = distanceToSqr(target) < 2.6 * 2.6;
		if (attackCooldown == 0 && close && (e.swing || distanceToSqr(target) < 1.4 * 1.4)) {
			attackCooldown = 20;
			doHurtTarget(level, target);
		} else if (e.swing && attackAnim == 0) {
			// повторяет замах впустую — и это видно
			attackAnim = 8;
			level.broadcastEntityEvent(this, EVENT_SWING);
		}
	}

	@Override
	public boolean doHurtTarget(ServerLevel level, Entity target) {
		attackAnim = 8;
		level.broadcastEntityEvent(this, EVENT_SWING);
		return super.doHurtTarget(level, target);
	}

	@Override
	public void handleEntityEvent(byte id) {
		if (id == EVENT_SWING) {
			attackAnim = 8;
		} else {
			super.handleEntityEvent(id);
		}
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		boolean hurt = super.hurtServer(level, source, amount);
		if (hurt) {
			level.sendParticles(ParticleTypes.WAX_OFF, getX(), getY(0.6), getZ(), 6, 0.25, 0.4, 0.25, 0.1);
		}
		return hurt;
	}

	@Override
	public int getMaxHeadYRot() {
		return 180;
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return random.nextInt(3) == 0 ? dev.celestial.registry.ModSounds.DOLL_MUSIC_BOX : null;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.COPPER_HIT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.COPPER_BREAK;
	}

	@Override
	protected void playStepSound(BlockPos pos, BlockState state) {
		playSound(SoundEvents.COPPER_STEP, 0.4F, 1.8F);
	}

	@Override
	public float getVoicePitch() {
		return 1.6F;
	}
}
