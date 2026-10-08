package dev.celestial.boss;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.HalfTransparentBlock;
import net.minecraft.world.level.block.state.BlockState;

/** Лёд ледяной тюрьмы Архонта: бьётся рукой за мгновение, ничего не роняет и сам тает через 10 с (софтлока нет). */
public class ArchonIceBlock extends HalfTransparentBlock {
	public ArchonIceBlock(Properties properties) {
		super(properties);
	}

	@Override
	protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState old, boolean moved) {
		if (!level.isClientSide()) {
			level.scheduleTick(pos, this, 200);
		}
	}

	@Override
	protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
	}
}
