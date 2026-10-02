package dev.celestial.world.dim;

import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.Level;

/**
 * Физика измерения мода.
 * gravity — добавка к множителю гравитации (−0.4 = 60% обычной), safeFall — сколько блоков падения без урона,
 * fallOutY/fallTarget/arrivalY — куда попадает тот, кто провалился ниже fallOutY (null — обычная смерть в пустоте).
 */
public record CelestialDimension(
	ResourceKey<Level> key,
	double gravity,
	double safeFall,
	int fallOutY,
	ResourceKey<Level> fallTarget,
	double arrivalY
) {}
