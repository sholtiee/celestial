package dev.celestial.light;

import dev.celestial.block.light.BeamFilterBlock;
import dev.celestial.block.light.BeamMirrorBlock;
import dev.celestial.block.light.BeamPrismBlock;
import dev.celestial.block.light.PeriscopeBlock;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashSet;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Трассировка лучей света. Одна и та же логика работает на сервере (попадания в цели)
 * и на клиенте (частицы вдоль луча), поэтому путь луча всегда совпадает с тем, что видит игрок.
 */
public final class LightBeams {
	/**
	 * Луч, который сейчас считается на сервере, выпущен «запечатанным» (родным) источником святилища. Приёмник святилища принимает только такой луч:
	 * свой фонарь, поставленный у приёмника, загадку не решает. Сервер однопоточный, значения не пересекаются.
	 */
	public static boolean sealedSource;

	/** Как часто источники пересчитывают луч (тики). */
	public static final int PULSE = 10;
	private static final int MAX_LENGTH = 64;
	private static final int MAX_SEGMENTS = 24;

	private LightBeams() {}

	/** Отрезок луча: от start (не включая) по направлению dir на length блоков. */
	public record Segment(BlockPos start, Direction dir, int length, LightColor color) {}

	public interface Visitor {
		default void segment(Segment segment) {}

		/** Луч упёрся в непрозрачный блок pos. */
		default void hit(BlockPos pos, BlockState state, LightColor color, Direction travel) {}
	}

	public static void trace(Level level, BlockPos source, Direction dir, LightColor color, Visitor visitor) {
		record Ray(BlockPos from, Direction dir, LightColor color) {}
		Deque<Ray> queue = new ArrayDeque<>();
		Set<Long> visited = new HashSet<>();
		queue.add(new Ray(source, dir, color));
		int segments = 0;
		int budget = MAX_LENGTH;
		while (!queue.isEmpty() && segments < MAX_SEGMENTS && budget > 0) {
			Ray ray = queue.poll();
			segments++;
			BlockPos.MutableBlockPos pos = ray.from().mutable();
			int length = 0;
			while (budget-- > 0) {
				pos.move(ray.dir());
				length++;
				if (!level.isLoaded(pos)) {
					break;
				}
				BlockState state = level.getBlockState(pos);
				long key = pos.asLong() * 31 + ray.dir().ordinal() * 7L + ray.color().ordinal();
				if (!visited.add(key)) {
					break; // петля из зеркал
				}
				if (state.getBlock() instanceof BeamMirrorBlock) {
					visitor.segment(new Segment(ray.from(), ray.dir(), length, ray.color()));
					queue.add(new Ray(pos.immutable(), BeamMirrorBlock.reflect(state, ray.dir()), ray.color()));
					break;
				}
				if (state.getBlock() instanceof PeriscopeBlock) {
					visitor.segment(new Segment(ray.from(), ray.dir(), length, ray.color()));
					queue.add(new Ray(pos.immutable(), PeriscopeBlock.redirect(state, ray.dir()), ray.color()));
					break;
				}
				if (state.getBlock() instanceof BeamPrismBlock && ray.dir().getAxis().isHorizontal()) {
					visitor.segment(new Segment(ray.from(), ray.dir(), length, ray.color()));
					if (ray.color() == LightColor.WHITE) {
						queue.add(new Ray(pos.immutable(), ray.dir().getCounterClockWise(), LightColor.RED));
						queue.add(new Ray(pos.immutable(), ray.dir(), LightColor.GREEN));
						queue.add(new Ray(pos.immutable(), ray.dir().getClockWise(), LightColor.BLUE));
					} else {
						queue.add(new Ray(pos.immutable(), ray.dir(), ray.color()));
					}
					break;
				}
				if (state.getBlock() instanceof BeamFilterBlock filter) {
					LightColor passes = filter.filter(ray.color());
					visitor.segment(new Segment(ray.from(), ray.dir(), length, ray.color()));
					if (passes != null) {
						queue.add(new Ray(pos.immutable(), ray.dir(), passes));
					}
					break;
				}
				if (!state.isAir() && (state.canOcclude() || state.getBlock() instanceof BeamTarget)) {
					visitor.segment(new Segment(ray.from(), ray.dir(), length - 1, ray.color()));
					visitor.hit(pos.immutable(), state, ray.color(), ray.dir());
					break;
				}
				if (budget == 0) {
					visitor.segment(new Segment(ray.from(), ray.dir(), length, ray.color()));
				}
			}
		}
	}
}
