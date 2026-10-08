package dev.celestial.boss;

import dev.celestial.data.CelestialData;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jspecify.annotations.Nullable;

/**
 * Ледяной шип Архонта. Сначала только метка — кольцо инея на земле (WARN тиков, есть время отбежать), потом шип вырастает
 * из пола (бьёт и подбрасывает всех над собой), стоит и рассыпается. Урон не наносит самому Архонту и его слугам.
 */
public class IceSpike extends Entity {
	public static final int WARN = 22;
	private static final int RISE = 4;
	private static final int LIFE = 70;
	private static final EntityDataAccessor<Integer> AGE = SynchedEntityData.defineId(IceSpike.class, EntityDataSerializers.INT);
	private @Nullable LivingEntity owner;
	private float damage = 9.0F;

	public IceSpike(EntityType<? extends IceSpike> type, Level level) {
		super(type, level);
		noPhysics = true;
	}

	public void setup(LivingEntity owner, float damage) {
		this.owner = owner;
		this.damage = damage;
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		builder.define(AGE, 0);
	}

	public int age() {
		return entityData.get(AGE);
	}

	/** 0 — ещё метка, 1 — шип в полный рост (для рендера, с учётом доли тика). */
	public float growth(float partial) {
		float a = age() + partial - WARN;
		if (a <= 0) {
			return 0;
		}
		float g = Math.min(1.0F, a / RISE);
		float fade = age() > LIFE - 10 ? Math.max(0, (LIFE - age() - partial) / 10.0F) : 1.0F;
		return g * fade;
	}

	@Override
	public void tick() {
		super.tick();
		int age = age() + 1;
		if (level() instanceof ServerLevel level) {
			entityData.set(AGE, age);
			if (age < WARN && age % 2 == 0) {  // метка: кольцо инея сжимается к центру
				double r = 1.6 * (1.0 - age / (double) WARN) + 0.4;
				for (int i = 0; i < 10; i++) {
					double a = i / 10.0 * Math.PI * 2 + age * 0.2;
					level.sendParticles(ParticleTypes.SNOWFLAKE, getX() + Math.cos(a) * r, getY() + 0.05, getZ() + Math.sin(a) * r, 1, 0, 0, 0, 0);
				}
			}
			if (age == WARN) {
				level.playSound(null, blockPosition(), dev.celestial.registry.ModSounds.SPIKE_RISE, SoundSource.HOSTILE, 1.4F, 0.9F + random.nextFloat() * 0.2F);
				level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState()),
					getX(), getY() + 0.2, getZ(), 30, 0.5, 0.2, 0.5, 0.2);
				strike(level);
			}
			if (age >= LIFE) {
				level.sendParticles(ParticleTypes.SNOWFLAKE, getX(), getY() + 1.2, getZ(), 20, 0.3, 0.8, 0.3, 0.03);
				discard();
			}
		}
	}

	private void strike(ServerLevel level) {
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(0.4, 0.5, 0.4))) {
			if (e == owner || e instanceof FrostArchon || e instanceof dev.celestial.entity.IceGuardian || e instanceof dev.celestial.entity.FrostWraith) {
				continue;
			}
			if (e instanceof Player p && (p.isCreative() || p.isSpectator())) {
				continue;
			}
			DamageSource src = owner != null ? damageSources().indirectMagic(this, owner) : damageSources().magic();
			if (e.hurtServer(level, src, damage)) {
				e.setDeltaMovement(e.getDeltaMovement().add(0, 0.75, 0));
				e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1));
				e.setTicksFrozen(Math.min(e.getTicksRequiredToFreeze() + 40, e.getTicksFrozen() + 80));
				if (e instanceof ServerPlayer sp) {
					sp.needsSync = true;
					CelestialData.update(sp, d -> d.withWarmth(d.warmth() - 8));
				}
			}
		}
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		return false;
	}

	@Override
	public boolean isPickable() {
		return false;
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		entityData.set(AGE, input.getIntOr("Age", 0));
		damage = input.getFloatOr("Damage", 9.0F);
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		output.putInt("Age", age());
		output.putFloat("Damage", damage);
	}
}
