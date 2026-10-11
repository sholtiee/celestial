package dev.celestial.mech;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Вал, шестерня или маховик: ось (как у брёвен — по грани, на которую ставишь) и вращение {@link #SPIN}:
 * 0 стоит, 1 по часовой, 2 против (анимированная текстура в обе стороны). Вращение ставит {@link Gears}.
 */
public class MechBlock extends Block implements Mech {
	public static final EnumProperty<Direction.Axis> AXIS = BlockStateProperties.AXIS;
	public static final IntegerProperty SPIN = IntegerProperty.create("spin", 0, 2);

	public enum Kind { SHAFT, GEAR, FLYWHEEL }

	private final Kind kind;
	private final VoxelShape[] shapes;

	public MechBlock(Kind kind, Properties properties) {
		super(properties);
		this.kind = kind;
		this.shapes = switch (kind) {
			case SHAFT -> new VoxelShape[] {Block.box(0, 6, 6, 16, 10, 10), Block.box(6, 0, 6, 10, 16, 10), Block.box(6, 6, 0, 10, 10, 16)};
			case GEAR -> new VoxelShape[] {Block.box(6, 0, 0, 10, 16, 16), Block.box(0, 6, 0, 16, 10, 16), Block.box(0, 0, 6, 16, 16, 10)};
			case FLYWHEEL -> new VoxelShape[] {Block.box(5, 0, 0, 11, 16, 16), Block.box(0, 5, 0, 16, 11, 16), Block.box(0, 0, 5, 16, 16, 11)};
		};
		registerDefaultState(stateDefinition.any().setValue(AXIS, Direction.Axis.Y).setValue(SPIN, 0));
	}

	public Kind kind() {
		return kind;
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(AXIS, SPIN);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		return defaultBlockState().setValue(AXIS, context.getClickedFace().getAxis());
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return shapes[state.getValue(AXIS).ordinal()];
	}

	@Override
	public boolean connects(BlockState state, Direction side) {
		return side.getAxis() == state.getValue(AXIS);
	}

	@Override
	public Direction.Axis axis(BlockState state) {
		return state.getValue(AXIS);
	}

	@Override
	public boolean meshes(BlockState state) {
		return kind == Kind.GEAR;
	}
}
