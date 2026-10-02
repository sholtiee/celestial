package dev.celestial.entity;

import dev.celestial.registry.ModEntities;
import dev.celestial.registry.ModItems;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.throwableitemprojectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;

/** Копьё Света: летит прямо, бьёт светом и подсвечивает цель, затем возвращается в руки хозяину. */
public class LightSpear extends ThrowableItemProjectile {
	private static final float DAMAGE = 10.0F;
	/** Копья, которые обрушивает босс: не возвращаются и исчезают при попадании. */
	private boolean hostile;

	public LightSpear(EntityType<? extends LightSpear> type, Level level) {
		super(type, level);
	}

	public LightSpear(Level level, LivingEntity owner, ItemStack stack) {
		super(ModEntities.LIGHT_SPEAR, owner, level, stack);
	}

	public static LightSpear hostile(Level level, LivingEntity caster, double x, double y, double z) {
		LightSpear spear = new LightSpear(ModEntities.LIGHT_SPEAR, level);
		spear.setOwner(caster);
		spear.setPos(x, y, z);
		spear.setItem(new ItemStack(ModItems.LIGHT_SPEAR));
		spear.hostile = true;
		spear.setDeltaMovement(0, -1.1, 0);
		return spear;
	}

	@Override
	protected Item getDefaultItem() {
		return ModItems.LIGHT_SPEAR;
	}

	@Override
	protected double getDefaultGravity() {
		return 0.005;
	}

	@Override
	public void tick() {
		super.tick();
		if (level().isClientSide()) {
			level().addParticle(ParticleTypes.END_ROD, getX(), getY(), getZ(), 0, 0, 0);
		} else if (tickCount > 60) {
			returnToOwner();
		}
	}

	@Override
	protected void onHitEntity(EntityHitResult hit) {
		super.onHitEntity(hit);
		Entity target = hit.getEntity();
		if (level() instanceof ServerLevel level && target != getOwner() && !(hostile && target instanceof FallenGuardian)) {
			target.hurtServer(level, damageSources().thrown(this, getOwner()), hostile ? 7.0F : DAMAGE);
			if (target instanceof LivingEntity living) {
				living.addEffect(new MobEffectInstance(MobEffects.GLOWING, 100), this);
			}
			level.sendParticles(ParticleTypes.END_ROD, target.getX(), target.getY(0.5), target.getZ(), 20, 0.3, 0.5, 0.3, 0.15);
		}
	}

	@Override
	protected void onHit(HitResult hit) {
		super.onHit(hit);
		if (!level().isClientSide()) {
			playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 1.0F, 1.6F);
			returnToOwner();
		}
	}

	/** Возвращаем копьё: в инвентарь хозяина или под ноги, если места нет. */
	private void returnToOwner() {
		if (isRemoved()) {
			return;
		}
		if (hostile) {
			if (level() instanceof ServerLevel level) {
				level.sendParticles(ParticleTypes.END_ROD, getX(), getY(), getZ(), 12, 0.4, 0.2, 0.4, 0.08);
			}
			discard();
			return;
		}
		ItemStack stack = getItem().copy();
		if (getOwner() instanceof Player player && player.isAlive()) {
			if (!player.getAbilities().instabuild && !player.getInventory().add(stack)) {
				spawnAtLocation((ServerLevel) level(), stack);
			}
			player.level().playSound(null, player.blockPosition(), SoundEvents.TRIDENT_RETURN, SoundSource.PLAYERS, 0.8F, 1.4F);
		} else if (level() instanceof ServerLevel level) {
			spawnAtLocation(level, stack);
		}
		discard();
	}
}
