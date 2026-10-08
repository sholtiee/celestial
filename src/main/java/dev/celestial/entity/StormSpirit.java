package dev.celestial.entity;

import java.util.EnumSet;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Blaze;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/** Грозовой дух: парит рядом с игроком и бьёт молнией издалека. */
public class StormSpirit extends Blaze {
	public StormSpirit(EntityType<? extends StormSpirit> type, Level level) {
		super(type, level);
		this.xpReward = 12;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
			.add(Attributes.MAX_HEALTH, 24.0)
			.add(Attributes.ATTACK_DAMAGE, 5.0)
			.add(Attributes.MOVEMENT_SPEED, 0.25)
			.add(Attributes.FOLLOW_RANGE, 40.0);
	}

	@Override
	protected void registerGoals() {
		this.goalSelector.addGoal(4, new StormStrikeGoal(this));
		this.goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 1.0, 0.0F));
		this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 12.0F));
		this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
		this.targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
		this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
	}

	@Override
	public boolean isOnFire() {
		return false;
	}

	/** Дух грозы — дитя дождя: в отличие от ифрита, вода и ливень ему не вредят (иначе на Грозовом пике духи таяли под дождём). */
	@Override
	public boolean isSensitiveToWater() {
		return false;
	}

	@Override
	public void thunderHit(ServerLevel level, LightningBolt lightningBolt) {
		// своя молния духу не вредит
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return SoundEvents.BREEZE_IDLE_AIR;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.BREEZE_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.BREEZE_DEATH;
	}

	/** Раз в несколько секунд — разряд молнии рядом с целью (с предупреждающими искрами). */
	static class StormStrikeGoal extends Goal {
		private final StormSpirit spirit;
		private int cooldown;
		private BlockPos marked;

		StormStrikeGoal(StormSpirit spirit) {
			this.spirit = spirit;
			this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
		}

		@Override
		public boolean canUse() {
			LivingEntity target = spirit.getTarget();
			return target != null && target.isAlive() && spirit.canAttack(target);
		}

		@Override
		public void start() {
			cooldown = 40;
			marked = null;
		}

		@Override
		public boolean requiresUpdateEveryTick() {
			return true;
		}

		@Override
		public void tick() {
			LivingEntity target = spirit.getTarget();
			if (target == null) {
				return;
			}
			spirit.getLookControl().setLookAt(target, 10.0F, 10.0F);
			double dist = spirit.distanceToSqr(target);
			// держимся на расстоянии 6..14 блоков и чуть выше цели
			Vec3 away = spirit.position().subtract(target.position()).normalize();
			double desired = dist < 36 ? 1.0 : dist > 196 ? -1.0 : 0.0;
			spirit.getMoveControl().setWantedPosition(
				spirit.getX() + away.x * desired * 3, target.getY() + 4.0, spirit.getZ() + away.z * desired * 3, 1.0);

			if (!(spirit.level() instanceof ServerLevel level) || !spirit.getSensing().hasLineOfSight(target)) {
				return;
			}
			cooldown--;
			if (cooldown == 20) {
				marked = target.blockPosition();
				level.sendParticles(net.minecraft.core.particles.ParticleTypes.ELECTRIC_SPARK,
					marked.getX() + 0.5, marked.getY() + 0.2, marked.getZ() + 0.5, 30, 0.6, 0.1, 0.6, 0.05);
				spirit.playSound(SoundEvents.TRIDENT_THUNDER.value(), 0.3F, 2.0F);
			} else if (cooldown <= 0 && marked != null) {
				LightningBolt bolt = EntityTypes.LIGHTNING_BOLT.create(level, EntitySpawnReason.TRIGGERED);
				if (bolt != null) {
					// молния только видимая: настоящая поджигала леса Рая (BUG-060); урон наносим сами тем, кто стоит на метке
					bolt.snapTo(Vec3.atBottomCenterOf(marked));
					bolt.setVisualOnly(true);
					level.addFreshEntity(bolt);
					for (net.minecraft.world.entity.LivingEntity e : level.getEntitiesOfClass(net.minecraft.world.entity.LivingEntity.class,
						new net.minecraft.world.phys.AABB(marked).inflate(1.5, 2.0, 1.5), e -> e != spirit && !(e instanceof StormSpirit))) {
						e.hurtServer(level, spirit.damageSources().lightningBolt(), 5.0F);
					}
				}
				cooldown = 70 + spirit.getRandom().nextInt(40);
				marked = null;
			}
		}
	}
}
