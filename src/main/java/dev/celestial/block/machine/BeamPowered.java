package dev.celestial.block.machine;

import dev.celestial.light.BeamTarget;
import dev.celestial.light.LightBeams;
import dev.celestial.light.LightColor;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/** Машина, питаемая лучом: помнит, когда в неё последний раз попал свет. */
public interface BeamPowered extends BeamTarget {
	Map<Long, Long> LAST_BEAM = new ConcurrentHashMap<>();

	@Override
	default void onBeamHit(ServerLevel level, BlockPos pos, BlockState state, LightColor color, Direction travel) {
		LAST_BEAM.put(key(level, pos), level.getGameTime());
	}

	static boolean isPowered(Level level, BlockPos pos) {
		Long last = LAST_BEAM.get(key(level, pos));
		return last != null && level.getGameTime() - last <= LightBeams.PULSE * 2;
	}

	private static long key(Level level, BlockPos pos) {
		return pos.asLong() * 31 + level.dimension().identifier().hashCode();
	}
}
