package dev.celestial.light;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;

/** Блок, который реагирует на попадание луча (приёмник, облачный лифт, машины). */
public interface BeamTarget {
	/** travel — направление, в котором летел луч. Вызывается каждые {@link LightBeams#PULSE} тиков, пока луч светит. */
	void onBeamHit(ServerLevel level, BlockPos pos, BlockState state, LightColor color, Direction travel);
}
