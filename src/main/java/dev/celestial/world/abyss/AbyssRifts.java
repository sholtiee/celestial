package dev.celestial.world.abyss;

import dev.celestial.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Поиск парного разлома в другом мире (та же x/z, радиус 12) и постройка нового, если его нет.
 * Разлом — квадрат 3×3 в полу площадки 7×7; игрок появляется на краю площадки (центр + (0, 1, 3)).
 */
public final class AbyssRifts {
	private static final int RADIUS = 12;

	private AbyssRifts() {}

	public static BlockPos findOrCreate(ServerLevel level, BlockPos near, boolean intoAbyss) {
		BlockPos found = find(level, near);
		if (found != null) {
			return center(level, found);
		}
		BlockPos center = intoAbyss ? abyssSpot(level, near) : new BlockPos(near.getX(), 100, near.getZ());
		build(level, center, intoAbyss);
		return center;
	}

	private static BlockPos find(ServerLevel level, BlockPos near) {
		BlockPos best = null;
		BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
		for (int dx = -RADIUS; dx <= RADIUS; dx++) {
			for (int dz = -RADIUS; dz <= RADIUS; dz++) {
				int x = near.getX() + dx;
				int z = near.getZ() + dz;
				for (int y = level.getMinY(); y < level.getMaxY(); y++) {
					p.set(x, y, z);
					if (level.getBlockState(p).is(ModBlocks.ABYSS_RIFT)
						&& (best == null || p.distSqr(near) < best.distSqr(near))) {
						best = p.immutable();
					}
				}
			}
		}
		return best;
	}

	/** Центр квадрата разлома: среднее по соседним блокам разлома. */
	private static BlockPos center(ServerLevel level, BlockPos any) {
		int sx = 0, sz = 0, n = 0;
		for (BlockPos p : BlockPos.betweenClosed(any.offset(-2, 0, -2), any.offset(2, 0, 2))) {
			if (level.getBlockState(p).is(ModBlocks.ABYSS_RIFT)) {
				sx += p.getX();
				sz += p.getZ();
				n++;
			}
		}
		return new BlockPos(Math.round((float) sx / n), any.getY(), Math.round((float) sz / n));
	}

	/** Место в Бездне: первый пол над уровнем озёр с запасом воздуха над ним; иначе площадка висит на высоте 70. */
	private static BlockPos abyssSpot(ServerLevel level, BlockPos near) {
		for (int y = 34; y < 180; y++) {
			BlockPos p = new BlockPos(near.getX(), y, near.getZ());
			if (level.getBlockState(p.below()).isSolid() && level.getBlockState(p).isAir() && level.getBlockState(p.above(3)).isAir()) {
				return p.below();
			}
		}
		return new BlockPos(near.getX(), 70, near.getZ());
	}

	private static void build(ServerLevel level, BlockPos center, boolean abyss) {
		BlockState floor = abyss ? ModBlocks.ABYSS_BRICKS.defaultBlockState() : ModBlocks.SKYSTONE_BRICKS.defaultBlockState();
		for (int dx = -3; dx <= 3; dx++) {
			for (int dz = -3; dz <= 3; dz++) {
				level.setBlockAndUpdate(center.offset(dx, 0, dz), floor);
				for (int dy = 1; dy <= 3; dy++) {
					level.setBlockAndUpdate(center.offset(dx, dy, dz), Blocks.AIR.defaultBlockState());
				}
			}
		}
		for (int dx = -1; dx <= 1; dx++) {
			for (int dz = -1; dz <= 1; dz++) {
				level.setBlockAndUpdate(center.offset(dx, 0, dz), ModBlocks.ABYSS_RIFT.defaultBlockState());
			}
		}
		if (abyss) {
			for (int[] c : new int[][] {{-3, -3}, {3, -3}, {-3, 3}, {3, 3}}) {
				level.setBlockAndUpdate(center.offset(c[0], 1, c[1]), ModBlocks.GLOWSHROOM_STEM.defaultBlockState());
				level.setBlockAndUpdate(center.offset(c[0], 2, c[1]), ModBlocks.SHADOW_CRYSTAL.defaultBlockState());
			}
		}
	}
}
