package dev.celestial.entity;

import dev.celestial.registry.ModEntities;
import dev.celestial.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.animal.equine.AbstractHorse;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/** Пегас: приручается манной, под седлом летает — удерживай прыжок, чтобы набрать высоту. */
public class Pegasus extends AbstractHorse {
	private static final double LIFT = 0.09, MAX_CLIMB = 0.42, GLIDE_FALL = -0.12;
	/** Порода: 0 — белый, 1 — золотой (Небесные сады), 2 — грозовой (Грозовой пик). */
	private static final net.minecraft.network.syncher.EntityDataAccessor<Integer> VARIANT =
		net.minecraft.network.syncher.SynchedEntityData.defineId(Pegasus.class, net.minecraft.network.syncher.EntityDataSerializers.INT);
	public static final int WHITE = 0, GOLDEN = 1, STORM = 2;

	public Pegasus(EntityType<? extends Pegasus> type, Level level) {
		super(type, level);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return createBaseHorseAttributes()
			.add(Attributes.MAX_HEALTH, 40.0)
			.add(Attributes.MOVEMENT_SPEED, 0.3)
			.add(Attributes.JUMP_STRENGTH, 0.9)
			.add(Attributes.SAFE_FALL_DISTANCE, 64.0);
	}

	@Override
	protected void defineSynchedData(net.minecraft.network.syncher.SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(VARIANT, WHITE);
	}

	public int getVariant() {
		return entityData.get(VARIANT);
	}

	public void setVariant(int variant) {
		entityData.set(VARIANT, Math.floorMod(variant, 3));
	}

	@Override
	protected void addAdditionalSaveData(net.minecraft.world.level.storage.ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putInt("Variant", getVariant());
	}

	@Override
	protected void readAdditionalSaveData(net.minecraft.world.level.storage.ValueInput input) {
		super.readAdditionalSaveData(input);
		setVariant(input.getIntOr("Variant", WHITE));
	}

	@Override
	public net.minecraft.world.entity.@Nullable SpawnGroupData finalizeSpawn(net.minecraft.world.level.ServerLevelAccessor level,
		net.minecraft.world.DifficultyInstance difficulty, EntitySpawnReason reason, net.minecraft.world.entity.@Nullable SpawnGroupData data) {
		var biome = level.getBiome(blockPosition());
		if (biome.is(dev.celestial.Celestial.id("heaven_gardens"))) {
			setVariant(random.nextInt(3) == 0 ? WHITE : GOLDEN);
		} else if (biome.is(dev.celestial.Celestial.id("storm_peak"))) {
			setVariant(STORM);
		} else {
			setVariant(random.nextInt(10) == 0 ? GOLDEN : WHITE);
		}
		return super.finalizeSpawn(level, difficulty, reason, data);
	}

	@Override
	public boolean isFood(ItemStack stack) {
		return stack.is(ModItems.MANNA_BERRIES);
	}

	@Override
	protected boolean handleEating(Player player, ItemStack stack) {
		if (!stack.is(ModItems.MANNA_BERRIES)) {
			return super.handleEating(player, stack);
		}
		boolean used = false;
		if (getHealth() < getMaxHealth()) {
			heal(4.0F);
			used = true;
		}
		if (!isTamed() && getTemper() < getMaxTemper()) {
			modifyTemper(8);
			used = true;
		}
		if (!level().isClientSide() && isTamed() && getAge() == 0 && !isInLove()) {
			setInLove(player);
			used = true;
		}
		if (used) {
			playSound(SoundEvents.HORSE_EAT, 1.0F, 1.2F);
		}
		return used;
	}

	@Override
	protected void tickRidden(Player controller, Vec3 riddenInput) {
		super.tickRidden(controller, riddenInput);
		if (!isLocalInstanceAuthoritative() || !isSaddled()) {
			return;
		}
		Vec3 motion = getDeltaMovement();
		if (controller.isJumping() && !onGround()) {
			// взмах крыльями: набираем высоту
			setDeltaMovement(motion.x, Math.min(motion.y + LIFT, MAX_CLIMB), motion.z);
		} else if (!onGround() && motion.y < GLIDE_FALL) {
			// без прыжка — плавно планируем
			setDeltaMovement(motion.x, GLIDE_FALL, motion.z);
		}
		resetFallDistance();
	}

	@Override
	protected float getRiddenSpeed(Player controller) {
		float base = super.getRiddenSpeed(controller);
		return onGround() ? base : base * 1.6F;
	}

	@Override
	public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
		return false;
	}

	@Override
	protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {
	}

	@Override
	public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
		if (!(partner instanceof Pegasus other)) {
			return null;
		}
		Pegasus foal = ModEntities.PEGASUS.create(level, EntitySpawnReason.BREEDING);
		if (foal != null) {
			// жеребёнок берёт породу одного из родителей, изредка — случайную
			foal.setVariant(random.nextInt(8) == 0 ? random.nextInt(3) : random.nextBoolean() ? getVariant() : other.getVariant());
		}
		return foal;
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return SoundEvents.HORSE_AMBIENT;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.HORSE_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.HORSE_DEATH;
	}

	@Override
	public float getVoicePitch() {
		return 1.3F;
	}
}
