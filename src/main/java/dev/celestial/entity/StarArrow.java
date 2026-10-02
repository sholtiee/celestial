package dev.celestial.entity;

import dev.celestial.registry.ModEntities;
import java.util.Comparator;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/** Звёздная стрела: в полёте плавно доворачивает к ближайшему врагу. */
public class StarArrow extends AbstractArrow {
	private static final double HOMING_RANGE = 16.0;
	private static final double TURN = 0.18;

	public StarArrow(EntityType<? extends StarArrow> type, Level level) {
		super(type, level);
	}

	public StarArrow(Level level, LivingEntity owner, ItemStack pickup, @Nullable ItemStack weapon) {
		super(ModEntities.STAR_ARROW, owner, level, pickup, weapon);
	}

	@Override
	public void tick() {
		super.tick();
		if (isInGround() || tickCount < 3) {
			return;
		}
		if (level().isClientSide()) {
			level().addParticle(ParticleTypes.END_ROD, getX(), getY(), getZ(), 0, 0, 0);
			return;
		}
		LivingEntity target = level().getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(HOMING_RANGE),
				e -> e instanceof Enemy && e.isAlive() && e != getOwner())
			.stream().min(Comparator.comparingDouble(this::distanceToSqr)).orElse(null);
		if (target != null) {
			Vec3 motion = getDeltaMovement();
			double speed = motion.length();
			Vec3 wanted = target.getBoundingBox().getCenter().subtract(position()).normalize().scale(speed);
			setDeltaMovement(motion.scale(1 - TURN).add(wanted.scale(TURN)).normalize().scale(speed));
			needsSync = true;
		}
	}

	@Override
	protected ItemStack getDefaultPickupItem() {
		return new ItemStack(Items.ARROW);
	}
}
