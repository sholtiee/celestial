package dev.celestial.world;

import dev.celestial.registry.ModBlocks;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/** Прямоугольная рамка из светлого камня: внутри 2..21 × 3..21 блоков воздуха. */
public record HeavenPortalShape(BlockPos bottomLeft, Direction.Axis axis, int width, int height) {
	public static final int MIN_WIDTH = 2, MIN_HEIGHT = 3, MAX_SIZE = 21;

	public static boolean isFrame(BlockState state) {
		return state.is(ModBlocks.RADIANT_STONE);
	}

	private static boolean isEmpty(BlockState state) {
		return state.isAir() || state.is(ModBlocks.HEAVEN_PORTAL) || state.canBeReplaced();
	}

	/** Ищет рамку, внутри которой находится {@code inside}, сначала по оси X, потом по Z. */
	public static Optional<HeavenPortalShape> find(LevelAccessor level, BlockPos inside) {
		for (Direction.Axis axis : new Direction.Axis[] {Direction.Axis.X, Direction.Axis.Z}) {
			Optional<HeavenPortalShape> shape = find(level, inside, axis);
			if (shape.isPresent()) {
				return shape;
			}
		}
		return Optional.empty();
	}

	public static Optional<HeavenPortalShape> find(LevelAccessor level, BlockPos inside, Direction.Axis axis) {
		if (!isEmpty(level.getBlockState(inside))) {
			return Optional.empty();
		}
		Direction left = axis == Direction.Axis.X ? Direction.WEST : Direction.NORTH;
		Direction right = left.getOpposite();
		// опускаемся до нижней кромки
		BlockPos pos = inside;
		for (int i = 0; i < MAX_SIZE && isEmpty(level.getBlockState(pos.below())); i++) {
			pos = pos.below();
		}
		if (!isFrame(level.getBlockState(pos.below()))) {
			return Optional.empty();
		}
		// идём влево до левой кромки
		for (int i = 0; i < MAX_SIZE && isEmpty(level.getBlockState(pos.relative(left))); i++) {
			pos = pos.relative(left);
		}
		if (!isFrame(level.getBlockState(pos.relative(left)))) {
			return Optional.empty();
		}
		BlockPos bottomLeft = pos;
		int width = 0;
		while (width <= MAX_SIZE && isEmpty(level.getBlockState(bottomLeft.relative(right, width)))) {
			if (!isFrame(level.getBlockState(bottomLeft.relative(right, width).below()))) {
				return Optional.empty();
			}
			width++;
		}
		if (width < MIN_WIDTH || width > MAX_SIZE || !isFrame(level.getBlockState(bottomLeft.relative(right, width)))) {
			return Optional.empty();
		}
		int height = 0;
		while (height <= MAX_SIZE && isEmpty(level.getBlockState(bottomLeft.above(height)))) {
			height++;
		}
		if (height < MIN_HEIGHT || height > MAX_SIZE) {
			return Optional.empty();
		}
		HeavenPortalShape shape = new HeavenPortalShape(bottomLeft, axis, width, height);
		return shape.isComplete(level) ? Optional.of(shape) : Optional.empty();
	}

	private Direction right() {
		return axis == Direction.Axis.X ? Direction.EAST : Direction.SOUTH;
	}

	/** Все внутренние клетки пусты, а по периметру — светлый камень. */
	public boolean isComplete(LevelAccessor level) {
		Direction right = right();
		for (int x = 0; x < width; x++) {
			if (!isFrame(level.getBlockState(bottomLeft.relative(right, x).below()))
				|| !isFrame(level.getBlockState(bottomLeft.relative(right, x).above(height)))) {
				return false;
			}
			for (int y = 0; y < height; y++) {
				if (!isEmpty(level.getBlockState(bottomLeft.relative(right, x).above(y)))) {
					return false;
				}
			}
		}
		for (int y = 0; y < height; y++) {
			if (!isFrame(level.getBlockState(bottomLeft.relative(right, -1).above(y)))
				|| !isFrame(level.getBlockState(bottomLeft.relative(right, width).above(y)))) {
				return false;
			}
		}
		return true;
	}

	public void fill(LevelAccessor level) {
		BlockState portal = ModBlocks.HEAVEN_PORTAL.defaultBlockState().setValue(HeavenPortalBlock.AXIS, axis);
		Direction right = right();
		for (int x = 0; x < width; x++) {
			for (int y = 0; y < height; y++) {
				level.setBlock(bottomLeft.relative(right, x).above(y), portal, Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
			}
		}
	}
}
