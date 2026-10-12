package dev.celestial.block.puzzle.time;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jspecify.annotations.Nullable;

/**
 * Циферблат загадки «Связанные часы»: висит на стене, стрелка показывает час (0 = двенадцать). ПКМ — стрелку вперёд на час,
 * ПКМ крадучись — назад. Циферблаты зала сцеплены шестернями по кругу: поворот одного двигает и следующий. Выставь каждый
 * на час со своей фрески над ним. Неразрушим.
 */
public class ClockDialBlock extends BaseEntityBlock implements dev.celestial.puzzle.PuzzleInteractive {
	public static final EnumProperty<Direction> FACING = HorizontalDirectionalBlock.FACING;
	public static final IntegerProperty HOUR = IntegerProperty.create("hour", 0, 11);
	private static final VoxelShape NORTH = Block.box(1, 1, 14, 15, 15, 16);
	private static final VoxelShape SOUTH = Block.box(1, 1, 0, 15, 15, 2);
	private static final VoxelShape WEST = Block.box(14, 1, 1, 16, 15, 15);
	private static final VoxelShape EAST = Block.box(0, 1, 1, 2, 15, 15);

	public ClockDialBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(HOUR, 0));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING, HOUR);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return switch (state.getValue(FACING)) {
			case SOUTH -> SOUTH;
			case WEST -> WEST;
			case EAST -> EAST;
			default -> NORTH;
		};
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new ClockDialBlockEntity(pos, state);
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (level instanceof ServerLevel server && level.getBlockEntity(pos) instanceof ClockDialBlockEntity dial) {
			dial.turn(server, player, player.isSecondaryUseActive() ? -1 : 1);
		}
		return InteractionResult.SUCCESS;
	}
}
