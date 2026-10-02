package dev.celestial.entity;

import dev.celestial.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomFlyingGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/** Облачная медуза: парит над островами, на неё можно встать — она подбрасывает высоко вверх. */
public class CloudJelly extends PathfinderMob {
	private int jellyCooldown;

	public CloudJelly(EntityType<? extends CloudJelly> type, Level level) {
		super(type, level);
		this.moveControl = new FlyingMoveControl<>(this, 10, true);
		this.setNoGravity(true);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes().add(Attributes.MAX_HEALTH, 12.0).add(Attributes.FLYING_SPEED, 0.04).add(Attributes.MOVEMENT_SPEED, 0.04);
	}

	@Override
	protected PathNavigation createNavigation(Level level) {
		return new FlyingPathNavigation(this, level);
	}

	@Override
	protected void registerGoals() {
		this.goalSelector.addGoal(5, new WaterAvoidingRandomFlyingGoal(this, 1.0));
	}

	@Override
	public void travel(Vec3 input) {
		this.travelFlying(input, this.getSpeed());
	}

	/** Медуза твёрдая сверху, как батут. */
	@Override
	public boolean canBeCollidedWith(Entity other) {
		return true;
	}

	@Override
	public boolean isPushable() {
		return false;
	}

	@Override
	public void tick() {
		super.tick();
		if (jellyCooldown > 0) {
			jellyCooldown--;
		}
		// подбрасываем тех, кто стоит на «куполе»
		for (Entity rider : level().getEntities(this, getBoundingBox().move(0, 0.3, 0).deflate(0.1, 0, 0.1))) {
			if (rider instanceof LivingEntity living && living.getY() >= getBoundingBox().maxY - 0.2) {
				living.setDeltaMovement(living.getDeltaMovement().x, 1.25, living.getDeltaMovement().z);
				living.resetFallDistance();
				living.needsSync = true;
				playSound(SoundEvents.SLIME_JUMP, 0.8F, 1.6F);
				if (level() instanceof ServerLevel server) {
					server.sendParticles(ParticleTypes.CLOUD, getX(), getBoundingBox().maxY, getZ(), 8, 0.4, 0.05, 0.4, 0.02);
				}
			}
		}
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (jellyCooldown == 0 && source.getEntity() instanceof Player) {
			spawnAtLocation(level, new ItemStack(ModItems.SKY_JELLY));
			jellyCooldown = 200;
		}
		return super.hurtServer(level, source, amount);
	}

	@Override
	public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
		return false;
	}

	@Override
	protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {
	}
}
