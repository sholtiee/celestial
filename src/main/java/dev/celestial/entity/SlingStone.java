package dev.celestial.entity;

import dev.celestial.registry.ModEntities;
import dev.celestial.registry.ModItems;
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

/**
 * Камень из пращи (1 Цар. 17:49): малый урон по малым целям и втрое больший по крупным — высоким (от 2,4 блока) или с запасом здоровья от 80.
 * Давид побеждает великана не силой, а метким камнем.
 */
public class SlingStone extends ThrowableItemProjectile {
	public static final float BASE_DAMAGE = 4.0F;
	public static final float BIG_FACTOR = 3.0F;

	public SlingStone(EntityType<? extends SlingStone> type, Level level) {
		super(type, level);
	}

	public SlingStone(Level level, LivingEntity owner) {
		super(ModEntities.SLING_STONE, owner, level, new ItemStack(ModItems.SLING_STONE));
	}

	/** Крупная цель: великан, голем, босс. */
	public static boolean isBig(Entity e) {
		return e.getBbHeight() >= 2.4F || e instanceof LivingEntity l && l.getMaxHealth() >= 80.0F;
	}

	@Override
	protected Item getDefaultItem() {
		return ModItems.SLING_STONE;
	}

	@Override
	public void tick() {
		super.tick();
		if (level() instanceof ServerLevel level && tickCount > 80) {
			discard();
		}
	}

	@Override
	protected void onHitEntity(EntityHitResult hit) {
		super.onHitEntity(hit);
		Entity target = hit.getEntity();
		if (!(level() instanceof ServerLevel level)) {
			return;
		}
		float damage = BASE_DAMAGE * (isBig(target) ? BIG_FACTOR : 1.0F);
		if (target.hurtServer(level, damageSources().thrown(this, getOwner()), damage) && isBig(target)) {
			level.sendParticles(ParticleTypes.CRIT, target.getX(), target.getY(0.8), target.getZ(), 14, 0.3, 0.4, 0.3, 0.2);
		}
	}

	@Override
	protected void onHit(HitResult hit) {
		super.onHit(hit);
		if (level() instanceof ServerLevel) {
			discard();
		}
	}
}
