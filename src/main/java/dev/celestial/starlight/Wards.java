package dev.celestial.starlight;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.Level;

/** Действующие Обереги по мирам: внутри радиуса нет Теней и не растёт страх тьмы. */
public final class Wards {
	public static final int RADIUS = 16;
	private static final Map<ResourceKey<Level>, Set<BlockPos>> ACTIVE = new HashMap<>();

	private Wards() {}

	static void set(Level level, BlockPos pos, boolean active) {
		Set<BlockPos> set = ACTIVE.computeIfAbsent(level.dimension(), k -> new HashSet<>());
		if (active) {
			set.add(pos.immutable());
		} else {
			set.remove(pos);
		}
	}

	public static boolean protects(Level level, BlockPos pos) {
		Set<BlockPos> set = ACTIVE.get(level.dimension());
		if (set == null || set.isEmpty()) {
			return false;
		}
		for (BlockPos ward : set) {
			if (ward.distSqr(pos) <= RADIUS * RADIUS) {
				return true;
			}
		}
		return false;
	}
}
