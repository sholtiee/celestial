package dev.celestial.block.light;

import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.EnumProperty;

/** Перископ: горизонтальный луч уходит вверх (или вниз), вертикальный — по горизонтали в сторону FACING. */
public class PeriscopeBlock extends Block implements Rotatable {
	public static final EnumProperty<Direction> FACING = BlockStateProperties.HORIZONTAL_FACING;
	public static final BooleanProperty UP = BooleanProperty.create("up");

	public PeriscopeBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(UP, true));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING, UP);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		return defaultBlockState().setValue(FACING, context.getHorizontalDirection()).setValue(UP, context.getClickedFace() != Direction.DOWN);
	}

	public static Direction redirect(BlockState state, Direction travel) {
		if (travel.getAxis().isHorizontal()) {
			return state.getValue(UP) ? Direction.UP : Direction.DOWN;
		}
		return state.getValue(FACING);
	}

	@Override
	public BlockState rotateWithFork(BlockState state) {
		// по кругу: север-вверх, восток-вверх, ..., запад-вниз
		Direction next = state.getValue(FACING).getClockWise();
		return next == Direction.NORTH ? state.setValue(FACING, next).cycle(UP) : state.setValue(FACING, next);
	}
}
