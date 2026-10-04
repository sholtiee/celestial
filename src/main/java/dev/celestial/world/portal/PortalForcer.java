package dev.celestial.world.portal;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;

/** Находит парный портал в целевом мире или строит новый на безопасном месте. */
public final class PortalForcer {
	private static final int SEARCH_RADIUS = 24;

	private PortalForcer() {}

	/** Возвращает позицию нижней клетки портала, куда ставить сущность. */
	public static BlockPos findOrCreate(PortalType type, ServerLevel level, BlockPos near, Direction.Axis axis) {
		BlockPos found = findExisting(type, level, near);
		return found != null ? found : create(type, level, near, axis);
	}

	private static BlockPos findExisting(PortalType type, ServerLevel level, BlockPos near) {
		BlockPos best = null;
		double bestDist = Double.MAX_VALUE;
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		for (int dx = -SEARCH_RADIUS; dx <= SEARCH_RADIUS; dx++) {
			for (int dz = -SEARCH_RADIUS; dz <= SEARCH_RADIUS; dz++) {
				int x = near.getX() + dx, z = near.getZ() + dz;
				int top = surfaceHeight(level, Heightmap.Types.WORLD_SURFACE, x, z);
				for (int y = Math.max(level.getMinY(), top - 48); y < top; y++) {  // портал стоит у поверхности: скан всей колонки был в разы дороже
					pos.set(x, y, z);
					if (level.getBlockState(pos).is(type.portal().get()) && !level.getBlockState(pos.below()).is(type.portal().get())) {
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

	private static BlockPos create(PortalType type, ServerLevel level, BlockPos near, Direction.Axis axis) {
		BlockPos base = level.dimension() == type.target() ? targetSpot(type, level, near) : surfaceSpot(level, near);
		build(type, level, base, axis);
		return base;
	}

	/** В Верхнем мире — просто поверхность в той же точке. */
	private static BlockPos surfaceSpot(ServerLevel level, BlockPos near) {
		int y = surfaceHeight(level, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, near.getX(), near.getZ());
		return new BlockPos(near.getX(), Math.max(y, level.getMinY() + 2), near.getZ());
	}

	/** В измерении мода — ближайшая подходящая поверхность по спирали, иначе — площадка на запасной высоте. */
	private static BlockPos targetSpot(PortalType type, ServerLevel level, BlockPos near) {
		// радиус не больше SEARCH_RADIUS: иначе на обратном пути исходный портал не находился и рядом строился второй
		for (int r = 0; r <= 20; r += 4) {
			for (int dx = -r; dx <= r; dx += 4) {
				for (int dz = -r; dz <= r; dz += 4) {
					if (Math.max(Math.abs(dx), Math.abs(dz)) != r) {
						continue;
					}
					int x = near.getX() + dx, z = near.getZ() + dz;
					int y = surfaceHeight(level, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
					BlockState ground = level.getBlockState(new BlockPos(x, y - 1, z));
					if (y > level.getMinY() + 30 && type.groundInTarget().test(ground)) {
						return new BlockPos(x, y, z);
					}
				}
			}
		}
		return new BlockPos(near.getX(), type.fallbackY(), near.getZ());
	}

	/** Высота поверхности с принудительной загрузкой чанка (Level.getHeight для незагруженного чанка вернёт дно мира). */
	private static int surfaceHeight(ServerLevel level, Heightmap.Types type, int x, int z) {
		return level.getChunk(x >> 4, z >> 4).getHeight(type, x & 15, z & 15) + 1;
	}

	/** Рамка 4×5 из светлого камня, портал 2×3 внутри и площадка под ногами. */
	private static void build(PortalType type, ServerLevel level, BlockPos base, Direction.Axis axis) {
		Direction right = axis == Direction.Axis.X ? Direction.EAST : Direction.SOUTH;
		Direction side = right.getClockWise();
		BlockState frame = type.frame().get().defaultBlockState();
		BlockState floor = level.dimension() == type.target() ? type.platform().get() : frame;
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
		new PortalShape(type, base, axis, 2, 3).fill(level);
	}
}
