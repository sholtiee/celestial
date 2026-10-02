package dev.celestial.world;

import dev.celestial.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;

/** Находит парный портал в целевом мире или строит новый на безопасном месте. */
public final class HeavenPortalForcer {
	private static final int SEARCH_RADIUS = 24;
	private static final int FALLBACK_HEAVEN_Y = 124;

	private HeavenPortalForcer() {}

	/** Возвращает позицию нижней клетки портала, куда ставить сущность. */
	public static BlockPos findOrCreate(ServerLevel level, BlockPos near, Direction.Axis axis) {
		BlockPos found = findExisting(level, near);
		return found != null ? found : create(level, near, axis);
	}

	private static BlockPos findExisting(ServerLevel level, BlockPos near) {
		BlockPos best = null;
		double bestDist = Double.MAX_VALUE;
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		for (int dx = -SEARCH_RADIUS; dx <= SEARCH_RADIUS; dx++) {
			for (int dz = -SEARCH_RADIUS; dz <= SEARCH_RADIUS; dz++) {
				int x = near.getX() + dx, z = near.getZ() + dz;
				int top = surfaceHeight(level, Heightmap.Types.WORLD_SURFACE, x, z);
				for (int y = level.getMinY(); y < top; y++) {
					pos.set(x, y, z);
					if (level.getBlockState(pos).is(ModBlocks.HEAVEN_PORTAL) && !level.getBlockState(pos.below()).is(ModBlocks.HEAVEN_PORTAL)) {
						double d = pos.distSqr(near);
						if (d < bestDist) {
							bestDist = d;
							best = pos.immutable();
						}
					}
				}
			}
		}
		return best;
	}

	private static BlockPos create(ServerLevel level, BlockPos near, Direction.Axis axis) {
		BlockPos base = HeavenDimension.isHeaven(level) ? heavenSpot(level, near) : surfaceSpot(level, near);
		build(level, base, axis);
		return base;
	}

	/** В Верхнем мире — просто поверхность в той же точке. */
	private static BlockPos surfaceSpot(ServerLevel level, BlockPos near) {
		int y = surfaceHeight(level, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, near.getX(), near.getZ());
		return new BlockPos(near.getX(), Math.max(y, level.getMinY() + 2), near.getZ());
	}

	/** В Раю — ближайший остров по спирали, иначе — облачная площадка в небе. */
	private static BlockPos heavenSpot(ServerLevel level, BlockPos near) {
		for (int r = 0; r <= 48; r += 4) {
			for (int dx = -r; dx <= r; dx += 4) {
				for (int dz = -r; dz <= r; dz += 4) {
					if (Math.max(Math.abs(dx), Math.abs(dz)) != r) {
						continue;
					}
					int x = near.getX() + dx, z = near.getZ() + dz;
					int y = surfaceHeight(level, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
					BlockState ground = level.getBlockState(new BlockPos(x, y - 1, z));
					if (y > level.getMinY() + 30 && (ground.is(ModBlocks.GOLDEN_GRASS) || ground.is(ModBlocks.SKYSTONE))) {
						return new BlockPos(x, y, z);
					}
				}
			}
		}
		return new BlockPos(near.getX(), FALLBACK_HEAVEN_Y, near.getZ());
	}

	/** Высота поверхности с принудительной загрузкой чанка (Level.getHeight для незагруженного чанка вернёт дно мира). */
	private static int surfaceHeight(ServerLevel level, Heightmap.Types type, int x, int z) {
		return level.getChunk(x >> 4, z >> 4).getHeight(type, x & 15, z & 15) + 1;
	}

	/** Рамка 4×5 из светлого камня, портал 2×3 внутри и площадка под ногами. */
	private static void build(ServerLevel level, BlockPos base, Direction.Axis axis) {
		Direction right = axis == Direction.Axis.X ? Direction.EAST : Direction.SOUTH;
		Direction side = right.getClockWise();
		BlockState frame = ModBlocks.RADIANT_STONE.defaultBlockState();
		BlockState floor = HeavenDimension.isHeaven(level) ? ModBlocks.SKYSTONE_BRICKS.defaultBlockState() : frame;
		int flags = Block.UPDATE_ALL;
		// площадка 4×3 и расчистка места
		for (int x = -1; x <= 2; x++) {
			for (int s = -1; s <= 1; s++) {
				BlockPos column = base.relative(right, x).relative(side, s);
				if (level.getBlockState(column.below()).canBeReplaced()) {
					level.setBlock(column.below(), floor, flags);
				}
				for (int y = 0; y <= 4; y++) {
					if (s != 0) {
						level.setBlock(column.above(y), Blocks.AIR.defaultBlockState(), flags);
					}
				}
			}
		}
		for (int x = -1; x <= 2; x++) {
			for (int y = -1; y <= 3; y++) {
				BlockPos p = base.relative(right, x).above(y);
				boolean edge = x == -1 || x == 2 || y == -1 || y == 3;
				level.setBlock(p, edge ? frame : Blocks.AIR.defaultBlockState(), flags);
			}
		}
		new HeavenPortalShape(base, axis, 2, 3).fill(level);
	}
}
