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

/** Сгусток пустоты — снаряд Безликого: летит прямо, ранит и на миг гасит свет вокруг (эффект «Тьма»). */
public class VoidBolt extends ThrowableItemProjectile {
	public VoidBolt(EntityType<? extends VoidBolt> type, Level level) {
		super(type, level);
	}

	public VoidBolt(EntityType<? extends VoidBolt> type, LivingEntity owner, Level level) {
		super(type, owner, level, new ItemStack(ModItems.SHADOW_ESSENCE));
		setNoGravity(true);
	}

	@Override
	protected Item getDefaultItem() {
		return ModItems.SHADOW_ESSENCE;
	}

	@Override
	public void tick() {
		super.tick();
		if (level() instanceof ServerLevel level) {
			level.sendParticles(dev.celestial.registry.ModParticles.SHADOW, getX(), getY(), getZ(), 1, 0.05, 0.05, 0.05, 0.0);
			if (tickCount > 100) {
				discard();
			}
		}
	}

	@Override
	protected void onHitEntity(EntityHitResult hit) {
		super.onHitEntity(hit);
		Entity target = hit.getEntity();
		if (target instanceof Faceless || !(level() instanceof ServerLevel level)) {
			return;
		}
		if (target.hurtServer(level, damageSources().indirectMagic(this, getOwner()), 6.0F) && target instanceof LivingEntity living) {
			living.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 50, 0));
		}
	}

	@Override
	protected void onHit(HitResult hit) {
		super.onHit(hit);
		if (level() instanceof ServerLevel level) {
			level.sendParticles(ParticleTypes.SQUID_INK, getX(), getY(), getZ(), 10, 0.2, 0.2, 0.2, 0.05);
			discard();
		}
	}
}
