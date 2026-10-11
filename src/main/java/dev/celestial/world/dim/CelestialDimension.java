package dev.celestial.world.dim;

import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.Level;

/**
 * Физика измерения мода.
 * gravity — добавка к множителю гравитации (−0.4 = 60% обычной), safeFall — сколько блоков падения без урона,
 * fallOutY/fallTarget/arrivalY — куда попадает тот, кто провалился ниже fallOutY (null — обычная смерть в пустоте);
 * space — невесомость: гравитация действует на всех живых (не только игроков), игрок «плывёт» (тяга прыжком на клиенте),
 * а провалившегося ниже fallOutY выносит на последний остров, где он стоял (fallTarget — само измерение).
 */
public record CelestialDimension(
	ResourceKey<Level> key,
	double gravity,
	double safeFall,
	int fallOutY,
	ResourceKey<Level> fallTarget,
	double arrivalY,
	boolean space
) {
	public CelestialDimension(ResourceKey<Level> key, double gravity, double safeFall, int fallOutY, ResourceKey<Level> fallTarget, double arrivalY) {
		this(key, gravity, safeFall, fallOutY, fallTarget, arrivalY, false);
	}
}
