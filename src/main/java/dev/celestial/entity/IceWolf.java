package dev.celestial.entity;

import dev.celestial.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.tags.ItemTags;
import net.minecraft.util.Mth;
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
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Ледяной волк — ездовой зверь Чертогов. Приручается сырой рыбой (как лошадь: корми и садись, пока не смирится), седлается.
 * Под седлом на льду и снегу бежит быстрее, под лапами вода схватывается льдом, а густая шерсть вдвое бережёт тепло седока.
 */
public class IceWolf extends AbstractHorse {
	public IceWolf(EntityType<? extends IceWolf> type, Level level) {
		super(type, level);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return createBaseHorseAttributes()
			.add(Attributes.MAX_HEALTH, 34.0)
			.add(Attributes.MOVEMENT_SPEED, 0.3)
			.add(Attributes.JUMP_STRENGTH, 0.8)
			.add(Attributes.SAFE_FALL_DISTANCE, 8.0);
	}

	@Override
	public boolean isFood(ItemStack stack) {
		return stack.is(ItemTags.FISHES);
	}

	@Override
	protected boolean handleEating(Player player, ItemStack stack) {
		if (!isFood(stack)) {
			return super.handleEating(player, stack);
		}
		boolean used = false;
		if (getHealth() < getMaxHealth()) {
			heal(5.0F);
			used = true;
		}
		if (!isTamed() && getTemper() < getMaxTemper()) {
			modifyTemper(10);
			used = true;
		}
		if (!level().isClientSide() && isTamed() && getAge() == 0 && !isInLove()) {
			setInLove(player);
			used = true;
		}
		if (used) {
			playSound(SoundEvents.FOX_SCREECH, 1.0F, 0.8F);
		}
		return used;
	}

	/** Под лапами лёд или снег — волк в своей стихии. */
	public boolean onIce() {
		BlockState below = level().getBlockState(getBlockPosBelowThatAffectsMyMovement());
		return below.is(BlockTags.ICE) || below.is(BlockTags.SNOW) || below.is(dev.celestial.registry.ModBlocks.FROST_STONE)
			|| below.is(dev.celestial.registry.ModBlocks.FROST_STONE_BRICKS);
	}

	@Override
	protected float getRiddenSpeed(Player controller) {
		float base = super.getRiddenSpeed(controller);
		return onIce() ? base * 1.45F : base;
	}

	@Override
	protected void tickRidden(Player controller, Vec3 riddenInput) {
		super.tickRidden(controller, riddenInput);
		if (level() instanceof ServerLevel server && isSaddled() && onGround()) {
			freezeWater(server);
		}
	}

	/** Как зачарование «Ледоход», только мощнее: вода под волком схватывается тающим льдом в радиусе 3. */
	private void freezeWater(ServerLevel level) {
		BlockPos center = blockPosition();
		int r = 3;
		BlockState frosted = Blocks.FROSTED_ICE.defaultBlockState();
		for (BlockPos p : BlockPos.betweenClosed(center.offset(-r, -1, -r), center.offset(r, -1, r))) {
			if (p.distToCenterSqr(getX(), p.getY() + 0.5, getZ()) > r * r) {
				continue;
			}
			BlockState state = level.getBlockState(p);
			if (state.getFluidState().is(FluidTags.WATER) && state.getFluidState().isSource() && state.is(Blocks.WATER)
				&& level.getBlockState(p.above()).isAir()) {
				level.setBlock(p, frosted, Block.UPDATE_ALL);
				level.scheduleTick(p, Blocks.FROSTED_ICE, Mth.nextInt(random, 60, 120));
			}
		}
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (level().isClientSide() && (isVehicle() || random.nextInt(3) == 0) && getDeltaMovement().horizontalDistanceSqr() > 0.002) {
			level().addParticle(ParticleTypes.SNOWFLAKE, getRandomX(0.6), getY() + 0.2, getRandomZ(0.6), 0, 0.02, 0);
		}
	}

	@Override
	public boolean canFreeze() {
		return false;
	}

	@Override
	public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
		return partner instanceof IceWolf ? ModEntities.ICE_WOLF.create(level, EntitySpawnReason.BREEDING) : null;
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return random.nextInt(4) == 0 ? SoundEvents.FOX_SCREECH : null;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.FOX_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.FOX_DEATH;
	}

	@Override
	protected void playStepSound(BlockPos pos, BlockState state) {
		playSound(SoundEvents.SNOW_STEP, 0.4F, 1.0F);
	}

	@Override
	public float getVoicePitch() {
		return 0.75F;
	}
}
