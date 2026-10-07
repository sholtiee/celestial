package dev.celestial.block.puzzle.ice;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Рунная глыба зала скользящего льда: ПКМ по боковой грани толкает её прочь от игрока, и она скользит до препятствия.
 * Неразрушима и не двигается поршнями. Высота столкновения полтора блока (как у забора) — на глыбу не запрыгнуть.
 */
public class GlacierRuneBlock extends Block implements dev.celestial.puzzle.PuzzleInteractive {
	private static final VoxelShape COLLISION = Block.box(0, 0, 0, 16, 24, 16);

	public GlacierRuneBlock(Properties properties) {
		super(properties);
	}

	@Override
	protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return COLLISION;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		Direction face = hit.getDirection();
		if (!face.getAxis().isHorizontal()) {
			return InteractionResult.SUCCESS;  // клик по верху ничего не делает, но и блок с руки не ставит
		}
		if (level instanceof ServerLevel server) {
			GlacierHallBlockEntity hall = hallOf(server, pos);
			if (hall != null) {
				hall.push(server, pos, face.getOpposite(), player);
			}
		}
		return InteractionResult.SUCCESS;
	}

	static GlacierHallBlockEntity hallOf(ServerLevel level, BlockPos pos) {
		for (BlockPos p : BlockPos.betweenClosed(pos.offset(-16, -4, -16), pos.offset(16, 4, 16))) {
			if (level.getBlockState(p).getBlock() instanceof IceBellBlock && level.getBlockEntity(p) instanceof GlacierHallBlockEntity hall
				&& hall.contains(level, pos)) {
				return hall;
			}
		}
		return null;
	}
}
