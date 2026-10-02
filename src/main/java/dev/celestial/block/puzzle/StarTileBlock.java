package dev.celestial.block.puzzle;

import dev.celestial.puzzle.PuzzleRewards;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Плитка-звезда («зажги все»): ПКМ переключает плитку и четырёх соседей.
 * Когда загорелись все плитки узора — узор застывает и даёт сигнал красного камня.
 */
public class StarTileBlock extends Block {
	public static final BooleanProperty LIT = BooleanProperty.create("lit");
	public static final BooleanProperty SOLVED = BooleanProperty.create("solved");
	private static final int MAX_PATTERN = 81;

	public StarTileBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(LIT, false).setValue(SOLVED, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(LIT, SOLVED);
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (state.getValue(SOLVED)) {
			return InteractionResult.PASS;
		}
		if (level instanceof ServerLevel server) {
			toggle(server, pos);
			for (Direction d : Direction.Plane.HORIZONTAL) {
				toggle(server, pos.relative(d));
			}
			server.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_STEP, SoundSource.BLOCKS, 1.0F, 1.5F);
			List<BlockPos> pattern = pattern(server, pos);
			if (pattern.stream().allMatch(p -> server.getBlockState(p).getValue(LIT))) {
				for (BlockPos p : pattern) {
					server.setBlock(p, server.getBlockState(p).setValue(SOLVED, true), Block.UPDATE_ALL);
				}
				PuzzleRewards.solved(server, pos, player, "star_tiles");
			}
		}
		return InteractionResult.SUCCESS;
	}

	private void toggle(ServerLevel level, BlockPos pos) {
		BlockState s = level.getBlockState(pos);
		if (s.is(this)) {
			level.setBlock(pos, s.cycle(LIT), Block.UPDATE_ALL);
		}
	}

	private List<BlockPos> pattern(ServerLevel level, BlockPos start) {
		List<BlockPos> out = new ArrayList<>();
		Deque<BlockPos> queue = new ArrayDeque<>(List.of(start));
		Set<BlockPos> seen = new HashSet<>();
		while (!queue.isEmpty() && out.size() < MAX_PATTERN) {
			BlockPos p = queue.poll();
			if (!seen.add(p) || !level.getBlockState(p).is(this)) {
				continue;
			}
			out.add(p);
			for (Direction d : Direction.Plane.HORIZONTAL) {
				queue.add(p.relative(d));
			}
		}
		return out;
	}

	@Override
	protected boolean isSignalSource(BlockState state) {
		return true;
	}

	@Override
	protected int getSignal(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
		return state.getValue(SOLVED) ? 15 : 0;
	}
}
