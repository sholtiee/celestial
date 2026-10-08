package dev.celestial.boss;

import dev.celestial.registry.ModItems;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.throwableitemprojectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;

/** Ледяной осколок — снаряд Архонта: летит прямо (без гравитации), ранит, замедляет и подмораживает. */
public class FrostShard extends ThrowableItemProjectile {
	public FrostShard(EntityType<? extends FrostShard> type, Level level) {
		super(type, level);
	}

	public FrostShard(EntityType<? extends FrostShard> type, LivingEntity owner, Level level) {
		super(type, owner, level, new ItemStack(ModItems.ICE_SHARD));
		setNoGravity(true);
	}

	@Override
	protected Item getDefaultItem() {
		return ModItems.ICE_SHARD;
	}

	@Override
	public void tick() {
		super.tick();
		if (level() instanceof ServerLevel level) {
			level.sendParticles(ParticleTypes.SNOWFLAKE, getX(), getY(), getZ(), 1, 0.05, 0.05, 0.05, 0.0);
			if (tickCount > 100) {
				discard();
			}
		}
	}

	@Override
	protected void onHitEntity(EntityHitResult hit) {
		super.onHitEntity(hit);
		Entity target = hit.getEntity();
		if (target instanceof FrostArchon || target instanceof dev.celestial.entity.IceGuardian || !(level() instanceof ServerLevel level)) {
			return;
		}
		if (target.hurtServer(level, damageSources().thrown(this, getOwner()), 6.0F) && target instanceof LivingEntity living) {
			living.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 50, 1));
			living.setTicksFrozen(Math.min(living.getTicksRequiredToFreeze() + 20, living.getTicksFrozen() + 50));
		}
	}

	@Override
	protected void onHit(HitResult hit) {
		super.onHit(hit);
		if (level() instanceof ServerLevel level) {
			level.sendParticles(ParticleTypes.SNOWFLAKE, getX(), getY(), getZ(), 12, 0.2, 0.2, 0.2, 0.08);
			discard();
		}
	}
}
