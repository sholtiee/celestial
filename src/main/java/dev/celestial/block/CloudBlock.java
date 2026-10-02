package dev.celestial.block;

import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.HalfTransparentBlock;
import net.minecraft.world.level.block.state.BlockState;

/** Облако: по нему можно ходить, а падение на него не наносит урона. */
public class CloudBlock extends HalfTransparentBlock {
	public CloudBlock(Properties properties) {
		super(properties);
	}

	@Override
	public void fallOn(Level level, BlockState state, BlockPos pos, Entity entity, double fallDistance) {
		entity.resetFallDistance();
	}
}
