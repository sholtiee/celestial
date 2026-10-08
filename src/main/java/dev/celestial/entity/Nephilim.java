package dev.celestial.entity;

import dev.celestial.data.CelestialData;
import dev.celestial.lore.Lore;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.network.chat.Component;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
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
import net.minecraft.world.phys.Vec3;

/**
 * Нефилим (Быт. 6:4) — великан Темницы Стражей, мини-босс Бездны. Медленный и тяжёлый: дубина бьёт сильно, а «топот» (с предупреждением — рука
 * поднимается) сбивает всех в радиусе 4,5. Большой и крепкий, но по крупным целям лучше всего работает праща (см. {@link SlingStone}).
 * Победа открывает лист Летописи «Исполины».
 */
public class Nephilim extends Monster {
	private static final byte EVENT_SWING = 4;
	private static final byte EVENT_SLAM = 61;
	private final ServerBossEvent bossEvent = new ServerBossEvent(java.util.UUID.randomUUID(), Component.translatable("entity.celestial.nephilim"),
		BossEvent.BossBarColor.RED, BossEvent.BossBarOverlay.PROGRESS);
	private int attackAnim;
	private int slamAnim;
	private int slamCooldown = 100;

	public Nephilim(EntityType<? extends Nephilim> type, Level level) {
		super(type, level);
		this.xpReward = 80;
		setPersistenceRequired();
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
			.add(Attributes.MAX_HEALTH, 260.0)
			.add(Attributes.ARMOR, 6.0)
			.add(Attributes.MOVEMENT_SPEED, 0.24)
			.add(Attributes.ATTACK_DAMAGE, 14.0)
			.add(Attributes.ATTACK_KNOCKBACK, 1.5)
			.add(Attributes.KNOCKBACK_RESISTANCE, 0.8)
			.add(Attributes.FOLLOW_RANGE, 28.0)
			.add(Attributes.STEP_HEIGHT, 1.0);
	}

	@Override
	protected void registerGoals() {
		goalSelector.addGoal(0, new FloatGoal(this));
		goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.0, true));
		goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.6));
		goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 12.0F));
		goalSelector.addGoal(8, new RandomLookAroundGoal(this));
		targetSelector.addGoal(1, new HurtByTargetGoal(this));
		targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
	}

	public float attackProgress(float partial) {
		return attackAnim > 0 ? (attackAnim - partial) / 10.0F : 0.0F;
	}

	/** 1 → 0: подъём и удар обеими руками (топот). */
	public float slamProgress(float partial) {
		return slamAnim > 0 ? (slamAnim - partial) / 24.0F : 0.0F;
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
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		bossEvent.setProgress(getHealth() / getMaxHealth());
		if (slamCooldown > 0) {
			slamCooldown--;
		}
		LivingEntity target = getTarget();
		if (target != null && slamCooldown == 0 && onGround() && distanceToSqr(target) < 20) {
			slamCooldown = 160 + random.nextInt(60);
			slamAnim = 24;
			level.broadcastEntityEvent(this, EVENT_SLAM);
			playSound(SoundEvents.RAVAGER_ROAR, 1.6F, 0.6F);
		}
		if (slamAnim == 1) {  // удар приходится на конец подъёма
			slam(level);
		}
	}

	private void slam(ServerLevel level) {
		level.playSound(null, blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.4F, 0.6F);
		for (int i = 0; i < 40; i++) {
			double a = i / 40.0 * Math.PI * 2;
			level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.DEEPSLATE.defaultBlockState()),
				getX() + Math.cos(a) * 3.5, getY() + 0.1, getZ() + Math.sin(a) * 3.5, 2, 0.2, 0.1, 0.2, 0.15);
		}
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(4.5, 1.0, 4.5), e -> e != this && e.isAlive())) {
			if (e instanceof Player p && (p.isCreative() || p.isSpectator())) {
				continue;
			}
			e.hurtServer(level, damageSources().mobAttack(this), 8.0F);
			Vec3 push = e.position().subtract(position()).multiply(1, 0, 1).normalize().scale(1.2);
			e.push(push.x, 0.5, push.z);
			if (e instanceof ServerPlayer sp) {
				sp.needsSync = true;
			}
		}
	}

	@Override
	public boolean doHurtTarget(ServerLevel level, Entity target) {
		attackAnim = 10;
		level.broadcastEntityEvent(this, EVENT_SWING);
		return super.doHurtTarget(level, target);
	}

	@Override
	public void handleEntityEvent(byte id) {
		if (id == EVENT_SWING) {
			attackAnim = 10;
		} else if (id == EVENT_SLAM) {
			slamAnim = 24;
		} else {
			super.handleEntityEvent(id);
		}
	}

	@Override
	public void die(DamageSource source) {
		super.die(source);
		if (level() instanceof ServerLevel level) {
			for (ServerPlayer p : level.getPlayers(p -> p.distanceToSqr(this) < 48 * 48)) {
				CelestialData.update(p, d -> d.withGrace(d.grace() + 3));
				Lore.unlock(p, "nephilim");
			}
			level.sendParticles(ParticleTypes.POOF, getX(), getY(1.0), getZ(), 60, 1.0, 1.5, 1.0, 0.05);
		}
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
	public boolean removeWhenFarAway(double distSqr) {
		return false;
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return SoundEvents.RAVAGER_AMBIENT;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.RAVAGER_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.RAVAGER_DEATH;
	}
}
