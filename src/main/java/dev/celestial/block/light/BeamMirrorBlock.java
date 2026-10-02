package dev.celestial.block.light;

import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;

/** Зеркало: диагональ «/» (flipped=false) или «\» (flipped=true). Поворачивается Камертоном. */
public class BeamMirrorBlock extends Block implements Rotatable {
	public static final BooleanProperty FLIPPED = BooleanProperty.create("flipped");

	public BeamMirrorBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(FLIPPED, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FLIPPED);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		Direction look = context.getHorizontalDirection();
		return defaultBlockState().setValue(FLIPPED, look == Direction.EAST || look == Direction.WEST);
	}

	/** Куда уйдёт луч, летевший в направлении travel. */
	public static Direction reflect(BlockState state, Direction travel) {
		if (!travel.getAxis().isHorizontal()) {
			return travel;
		}
		boolean flipped = state.getValue(FLIPPED);
		return switch (travel) {
			case NORTH -> flipped ? Direction.WEST : Direction.EAST;
			case SOUTH -> flipped ? Direction.EAST : Direction.WEST;
			case EAST -> flipped ? Direction.SOUTH : Direction.NORTH;
			default -> flipped ? Direction.NORTH : Direction.SOUTH;
		};
	}

	@Override
	public BlockState rotateWithFork(BlockState state) {
		return state.cycle(FLIPPED);
	}
}
