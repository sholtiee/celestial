package dev.celestial.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.InsideBlockEffectApplier;
import net.minecraft.world.entity.InsideBlockEffectType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/** Дождевое облако: проходимое, замедляет падение, тушит огонь и роняет капли. */
public class RainCloudBlock extends CloudBlock {
	public RainCloudBlock(Properties properties) {
		super(properties);
	}

	@Override
	protected void entityInside(BlockState state, Level level, BlockPos pos, Entity entity, InsideBlockEffectApplier effectApplier, boolean isPrecise) {
		effectApplier.apply(InsideBlockEffectType.EXTINGUISH);
		entity.makeStuckInBlock(state, new Vec3(0.9, 0.4, 0.9));
		entity.resetFallDistance();
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		if (random.nextInt(3) == 0 && level.getBlockState(pos.below()).isAir()) {
			level.addParticle(ParticleTypes.DRIPPING_WATER, pos.getX() + random.nextDouble(), pos.getY() - 0.05, pos.getZ() + random.nextDouble(), 0, 0, 0);
		}
	}
}
