package dev.celestial.entity;

import dev.celestial.Celestial;
import java.util.EnumSet;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomFlyingGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Голубь-проводник (Быт. 8:11): принёс масличный лист — вода сошла, дорога есть. Призывается Масличной ветвью, летит впереди хозяина к ближайшей постройке из тега
 * `celestial:dove_guides_to` (все места Кодекса) и через несколько минут улетает. Голуби в голубятне Ковчега — декор (NoAI).
 */
public class Dove extends PathfinderMob {
	public static final TagKey<Structure> TARGETS = TagKey.create(Registries.STRUCTURE, Celestial.id("dove_guides_to"));
	public static final int LIFETIME = 6000;
	private @Nullable UUID owner;
	private int age;

	public Dove(EntityType<? extends Dove> type, Level level) {
		super(type, level);
		this.moveControl = new FlyingMoveControl(this, 20, true);
		setNoGravity(true);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes().add(Attributes.MAX_HEALTH, 6.0).add(Attributes.FLYING_SPEED, 0.2).add(Attributes.MOVEMENT_SPEED, 0.2);
	}

	public void setOwner(Player player) {
		this.owner = player.getUUID();
	}

	public @Nullable UUID owner() {
		return owner;
	}

	@Override
	protected PathNavigation createNavigation(Level level) {
		FlyingPathNavigation nav = new FlyingPathNavigation(this, level);
		nav.setCanFloat(true);
		return nav;
	}

	@Override
	protected void registerGoals() {
		goalSelector.addGoal(2, new GuideGoal());
		goalSelector.addGoal(6, new WaterAvoidingRandomFlyingGoal(this, 1.0));
		goalSelector.addGoal(8, new RandomLookAroundGoal(this));
	}

	@Override
	public void travel(Vec3 input) {
		travelFlying(input, getSpeed());
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (level().isClientSide() && random.nextInt(6) == 0) {
			level().addParticle(ParticleTypes.END_ROD, getRandomX(0.3), getRandomY(), getRandomZ(0.3), 0, -0.01, 0);
		}
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (owner != null && ++age > LIFETIME) {
			level.sendParticles(ParticleTypes.CLOUD, getX(), getY(0.5), getZ(), 10, 0.2, 0.2, 0.2, 0.02);
			discard();
		}
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		return source.is(net.minecraft.tags.DamageTypeTags.BYPASSES_INVULNERABILITY) && super.hurtServer(level, source, amount);
	}

	@Override
	public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
		return false;
	}

	@Override
	protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {
	}

	@Override
	public boolean removeWhenFarAway(double distSqr) {
		return owner != null;
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		if (owner != null) {
			output.putString("Owner", owner.toString());
			output.putInt("Age", age);
		}
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		String id = input.getStringOr("Owner", "");
		owner = id.isEmpty() ? null : UUID.fromString(id);
		age = input.getIntOr("Age", 0);
	}

	/** Летит на 5–6 блоков впереди хозяина по прямой к ближайшей постройке; у цели кружит и остаётся. */
	private class GuideGoal extends Goal {
		private Player follower;
		private BlockPos destination;
		private int recalc;
		private boolean arrived;

		GuideGoal() {
			setFlags(EnumSet.of(Goal.Flag.MOVE));
		}

		@Override
		public boolean canUse() {
			if (owner == null || !(level() instanceof ServerLevel server)) {
				return false;
			}
			follower = server.getPlayerByUUID(owner);
			return follower != null && follower.isAlive() && distanceToSqr(follower) < 40 * 40;
		}

		@Override
		public boolean canContinueToUse() {
			return canUse();
		}

		@Override
		public void start() {
			recalc = 0;
		}

		@Override
		public void tick() {
			if (--recalc <= 0) {
				recalc = 1200;  // поиск синхронный и догенерирует чанки — раз в минуту
				if (level() instanceof ServerLevel server) {
					destination = server.findNearestMapStructure(TARGETS, follower.blockPosition(), 24, false);
					if (destination == null && follower instanceof ServerPlayer sp && !arrived) {
						sp.sendOverlayMessage(Component.translatable("entity.celestial.dove.nothing"));
					}
				}
			}
			if (destination == null) {
				getMoveControl().setWantedPosition(follower.getX() + Math.sin(tickCount * 0.05) * 2, follower.getEyeY() + 0.8, follower.getZ() + Math.cos(tickCount * 0.05) * 2, 1.0);
				return;
			}
			double dx = destination.getX() - follower.getX();
			double dz = destination.getZ() - follower.getZ();
			double len = Math.max(1.0, Math.sqrt(dx * dx + dz * dz));
			if (len < 14 && !arrived) {
				arrived = true;
				if (follower instanceof ServerPlayer sp) {
					sp.sendOverlayMessage(Component.translatable("entity.celestial.dove.arrived"));
				}
			}
			double lead = arrived ? 0.0 : Math.min(6.0, len);
			getMoveControl().setWantedPosition(follower.getX() + dx / len * lead, follower.getEyeY() + 0.8 + (arrived ? Math.sin(tickCount * 0.1) : 0), follower.getZ() + dz / len * lead, 1.3);
		}
	}
}
