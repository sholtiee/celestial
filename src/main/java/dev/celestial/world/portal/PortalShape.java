package dev.celestial.world.portal;

import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/** Прямоугольная рамка портала: внутри 2..21 × 3..21 блоков воздуха, углы необязательны. */
public record PortalShape(PortalType type, BlockPos bottomLeft, Direction.Axis axis, int width, int height) {
	public static final int MIN_WIDTH = 2, MIN_HEIGHT = 3, MAX_SIZE = 21;

	private static boolean isEmpty(PortalType type, BlockState state) {
		return state.isAir() || state.is(type.portal().get()) || state.canBeReplaced();
	}

	/** Ищет рамку, внутри которой находится {@code inside}, сначала по оси X, потом по Z. */
	public static Optional<PortalShape> find(PortalType type, LevelAccessor level, BlockPos inside) {
		for (Direction.Axis axis : new Direction.Axis[] {Direction.Axis.X, Direction.Axis.Z}) {
			Optional<PortalShape> shape = find(type, level, inside, axis);
			if (shape.isPresent()) {
				return shape;
			}
		}
		return Optional.empty();
	}

	public static Optional<PortalShape> find(PortalType type, LevelAccessor level, BlockPos inside, Direction.Axis axis) {
		if (!isEmpty(type, level.getBlockState(inside))) {
			return Optional.empty();
		}
		Direction left = axis == Direction.Axis.X ? Direction.WEST : Direction.NORTH;
		Direction right = left.getOpposite();
		// опускаемся до нижней кромки
		BlockPos pos = inside;
		for (int i = 0; i < MAX_SIZE && isEmpty(type, level.getBlockState(pos.below())); i++) {
			pos = pos.below();
		}
		if (!type.isFrame(level.getBlockState(pos.below()))) {
			return Optional.empty();
		}
		// идём влево до левой кромки
		for (int i = 0; i < MAX_SIZE && isEmpty(type, level.getBlockState(pos.relative(left))); i++) {
			pos = pos.relative(left);
		}
		if (!type.isFrame(level.getBlockState(pos.relative(left)))) {
			return Optional.empty();
		}
		BlockPos bottomLeft = pos;
		int width = 0;
		while (width <= MAX_SIZE && isEmpty(type, level.getBlockState(bottomLeft.relative(right, width)))) {
			if (!type.isFrame(level.getBlockState(bottomLeft.relative(right, width).below()))) {
				return Optional.empty();
			}
			width++;
		}
		if (width < MIN_WIDTH || width > MAX_SIZE || !type.isFrame(level.getBlockState(bottomLeft.relative(right, width)))) {
			return Optional.empty();
		}
		int height = 0;
		while (height <= MAX_SIZE && isEmpty(type, level.getBlockState(bottomLeft.above(height)))) {
			height++;
		}
		if (height < MIN_HEIGHT || height > MAX_SIZE) {
			return Optional.empty();
		}
		PortalShape shape = new PortalShape(type, bottomLeft, axis, width, height);
		return shape.isComplete(level) ? Optional.of(shape) : Optional.empty();
	}

	private Direction right() {
		return axis == Direction.Axis.X ? Direction.EAST : Direction.SOUTH;
	}

	/** Все внутренние клетки пусты, а по периметру — светлый камень. */
	public boolean isComplete(LevelAccessor level) {
		Direction right = right();
		for (int x = 0; x < width; x++) {
			if (!type.isFrame(level.getBlockState(bottomLeft.relative(right, x).below()))
				|| !type.isFrame(level.getBlockState(bottomLeft.relative(right, x).above(height)))) {
				return false;
			}
			for (int y = 0; y < height; y++) {
				if (!isEmpty(type, level.getBlockState(bottomLeft.relative(right, x).above(y)))) {
					return false;
				}
			}
		}
		for (int y = 0; y < height; y++) {
			if (!type.isFrame(level.getBlockState(bottomLeft.relative(right, -1).above(y)))
				|| !type.isFrame(level.getBlockState(bottomLeft.relative(right, width).above(y)))) {
				return false;
			}
		}
		return true;
	}

	public void fill(LevelAccessor level) {
		BlockState portal = type.portal().get().defaultBlockState().setValue(CelestialPortalBlock.AXIS, axis);
		Direction right = right();
		for (int x = 0; x < width; x++) {
			for (int y = 0; y < height; y++) {
				level.setBlock(bottomLeft.relative(right, x).above(y), portal, Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
			}
		}
	}
}
