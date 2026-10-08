package dev.celestial.block.eden;

import dev.celestial.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Роса-манна (Исх. 16): утром лежит на золотой траве Рая, ПКМ — собрать; к полудню тает (Исх. 16:21). */
public class MannaDewBlock extends Block {
	private static final VoxelShape SHAPE = Block.box(2, 0, 2, 14, 2, 14);

	public MannaDewBlock(Properties properties) {
		super(properties);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	@Override
	protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
		return level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), net.minecraft.core.Direction.UP);
	}

	@Override
	protected BlockState updateShape(BlockState state, LevelReader level, net.minecraft.world.level.ScheduledTickAccess ticks, BlockPos pos,
		net.minecraft.core.Direction direction, BlockPos neighborPos, BlockState neighborState, RandomSource random) {
		return canSurvive(state, level, pos) ? state : net.minecraft.world.level.block.Blocks.AIR.defaultBlockState();
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (level instanceof ServerLevel server) {
			server.removeBlock(pos, false);
			Block.popResource(server, pos, new ItemStack(ModItems.MANNA, 1 + server.getRandom().nextInt(2)));
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	protected void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		long time = level.getOverworldClockTime() % 24000L;
		if (time >= 6000L && time < 22000L) {  // к полудню роса тает
			level.removeBlock(pos, false);
		}
	}

	@Override
	protected boolean isRandomlyTicking(BlockState state) {
		return true;
	}
}
