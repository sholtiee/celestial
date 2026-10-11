package dev.celestial.mech;

import net.minecraft.core.Direction;
import net.minecraft.world.level.block.state.BlockState;

/** Деталь сети оборотов: передаёт вращение через грани (соосно) и, у шестерён, зацеплением с соседними шестернями. */
public interface Mech {
	/** Передаёт ли деталь вращение через эту грань (соосно). */
	boolean connects(BlockState state, Direction side);

	/** Ось вращения. */
	Direction.Axis axis(BlockState state);

	/** Шестерня: зацепляется с соседними шестернями той же оси в плоскости вращения (направление меняется). */
	default boolean meshes(BlockState state) {
		return false;
	}
}
