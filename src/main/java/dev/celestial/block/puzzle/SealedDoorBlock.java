package dev.celestial.block.puzzle;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashSet;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.redstone.Orientation;
import org.jspecify.annotations.Nullable;

/**
 * Печать-дверь: неразрушимая стена святилищ. Растворяется целиком (все соседние блоки печати) только по решению загадки
 * ({@link dev.celestial.puzzle.PuzzleRewards}, испытание). На редстоун не реагирует: рычаг рядом раньше открывал любую дверь.
 */
public class SealedDoorBlock extends Block {
	private static final int MAX_BLOCKS = 128;

	public SealedDoorBlock(Properties properties) {
		super(properties);
	}

	public static void dissolve(ServerLevel level, BlockPos start) {
		Deque<BlockPos> queue = new ArrayDeque<>();
		Set<BlockPos> seen = new HashSet<>();
		queue.add(start);
		Block self = level.getBlockState(start).getBlock();
		while (!queue.isEmpty() && seen.size() < MAX_BLOCKS) {
			BlockPos pos = queue.poll();
			if (!seen.add(pos) || level.getBlockState(pos).getBlock() != self) {
				continue;
			}
			level.setBlock(pos, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
			level.sendParticles(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 4, 0.3, 0.3, 0.3, 0.05);
			for (Direction d : Direction.values()) {
				queue.add(pos.relative(d));
			}
		}
		level.playSound(null, start, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 1.5F, 1.4F);
	}
}
