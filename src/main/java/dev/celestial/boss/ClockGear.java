package dev.celestial.boss;

import dev.celestial.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.throwableitemprojectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Шестерня Часовщика: катится по полу прямо (без гравитации, держится пола), бьёт и отбрасывает, в стену — рассыпается.
 * Снаряд принадлежит боссу, поэтому в его «Стой!» не замирает.
 */
public class ClockGear extends ThrowableItemProjectile {
	public static final float DAMAGE = 7.0F;
	private static final int LIFE = 110;

	public ClockGear(EntityType<? extends ClockGear> type, Level level) {
		super(type, level);
		setNoGravity(true);
	}

	public ClockGear(EntityType<? extends ClockGear> type, LivingEntity owner, Level level) {
		super(type, owner, level, new ItemStack(ModBlocks.GEAR.asItem()));
		setNoGravity(true);
	}

	@Override
	protected Item getDefaultItem() {
		return ModBlocks.GEAR.asItem();
	}

	@Override
	public void tick() {
		// держится пола: над пустотой падает, на полу — скользит по его верху
		Vec3 m = getDeltaMovement();
		BlockPos below = BlockPos.containing(getX(), getY() - 0.05, getZ());
		boolean grounded = !level().getBlockState(below).getCollisionShape(level(), below).isEmpty();
		setDeltaMovement(m.x, grounded ? 0.0 : Math.max(-0.6, m.y - 0.08), m.z);
		if (grounded) {
			setPos(getX(), below.getY() + 1.02, getZ());
		}
		super.tick();
		if (level() instanceof ServerLevel level) {
			if (tickCount % 2 == 0) {
				level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 0.05, getZ(), 1, 0.1, 0.0, 0.1, 0.02);
			}
			if (tickCount > LIFE) {
				burst(level);
			}
		}
	}

	@Override
	protected void onHitEntity(EntityHitResult hit) {
		super.onHitEntity(hit);
		Entity target = hit.getEntity();
		if (target instanceof Clockmaker || target instanceof ClockGear || !(level() instanceof ServerLevel level)) {
			return;
		}
		float dmg = dev.celestial.chrono.TimeFlow.scale(target) <= 0 ? DAMAGE * 0.5F : DAMAGE;  // по застывшему в «Стой!» — вполсилы
		if (target.hurtServer(level, damageSources().thrown(this, getOwner()), dmg) && target instanceof LivingEntity living) {
			Vec3 push = getDeltaMovement().normalize().scale(0.7);
			living.push(push.x, 0.3, push.z);
			if (living instanceof net.minecraft.server.level.ServerPlayer sp) {
				sp.syncVelocity = true;
			}
		}
	}

	@Override
	protected void onHit(HitResult hit) {
		super.onHit(hit);
		if (level() instanceof ServerLevel level) {
			burst(level);
		}
	}

	private void burst(ServerLevel level) {
		level.sendParticles(ParticleTypes.CRIT, getX(), getY() + 0.2, getZ(), 10, 0.2, 0.2, 0.2, 0.15);
		discard();
	}
}
