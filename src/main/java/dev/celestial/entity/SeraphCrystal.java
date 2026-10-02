package dev.celestial.entity;

import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jspecify.annotations.Nullable;

/** Кристалл света на арене Серафима: лучом лечит босса. Разбивается одним ударом или стрелой (без взрыва). */
public class SeraphCrystal extends Entity {
	private static final EntityDataAccessor<Optional<BlockPos>> BEAM = SynchedEntityData.defineId(SeraphCrystal.class, EntityDataSerializers.OPTIONAL_BLOCK_POS);
	public int time;

	public SeraphCrystal(EntityType<? extends SeraphCrystal> type, Level level) {
		super(type, level);
		this.blocksBuilding = true;
		this.time = random.nextInt(100000);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		builder.define(BEAM, Optional.empty());
	}

	public void setBeamTarget(@Nullable BlockPos target) {
		entityData.set(BEAM, Optional.ofNullable(target));
	}

	public @Nullable BlockPos getBeamTarget() {
		return entityData.get(BEAM).orElse(null);
	}

	@Override
	public void tick() {
		super.tick();
		time++;
		if (level().isClientSide() && random.nextInt(4) == 0) {
			level().addParticle(ParticleTypes.END_ROD, getRandomX(0.6), getRandomY(), getRandomZ(0.6), 0, 0.02, 0);
		}
	}

	@Override
	public boolean isPickable() {
		return true;
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
		if (isInvulnerableToBase(source) || isRemoved()) {
			return false;
		}
		level.sendParticles(ParticleTypes.END_ROD, getX(), getY(0.5), getZ(), 60, 0.4, 0.6, 0.4, 0.25);
		level.playSound(null, blockPosition(), SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 2.0F, 0.6F);
		level.playSound(null, blockPosition(), dev.celestial.registry.ModSounds.CRYSTAL_BREAK, SoundSource.HOSTILE, 2.0F, 1.0F);
		remove(RemovalReason.KILLED);
		return true;
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		output.storeNullable("beam_target", BlockPos.CODEC, getBeamTarget());
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		setBeamTarget(input.read("beam_target", BlockPos.CODEC).orElse(null));
	}

	@Override
	public boolean shouldRenderAtSqrDistance(double distance) {
		return super.shouldRenderAtSqrDistance(distance) || getBeamTarget() != null;
	}
}
