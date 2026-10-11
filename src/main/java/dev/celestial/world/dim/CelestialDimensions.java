package dev.celestial.world.dim;

import dev.celestial.world.HeavenDimension;
import java.util.List;
import net.minecraft.world.level.Level;
import org.jspecify.annotations.Nullable;

/** Профили всех измерений мода. */
public final class CelestialDimensions {
	public static final CelestialDimension HEAVEN = new CelestialDimension(HeavenDimension.HEAVEN, -0.4, 6.0, -24, Level.OVERWORLD, 300.0);

	/** Бездна: обычная гравитация, выпасть некуда (бедрок сверху и снизу). */
	public static final CelestialDimension ABYSS = new CelestialDimension(AbyssFeatures.ABYSS, 0.0, 0.0, -64, null, 0.0);

	/** Ледяные Чертоги: обычная физика, упасть в пустоту — смерть, как в Верхнем мире. */
	public static final CelestialDimension FROZEN_HALLS = new CelestialDimension(AbyssFeatures.FROZEN_HALLS, 0.0, 0.0, -128, null, 0.0);

	/** Астрал: гравитация ×0.15 для всех живых, падение без урона, из пустоты выносит на последний остров. */
	public static final CelestialDimension ASTRAL = new CelestialDimension(AbyssFeatures.ASTRAL, -0.85, 1000.0, -16, AbyssFeatures.ASTRAL, 128.0, true);

	public static final List<CelestialDimension> ALL = List.of(HEAVEN, ABYSS, FROZEN_HALLS, ASTRAL);

	private CelestialDimensions() {}

	public static @Nullable CelestialDimension of(Level level) {
		for (CelestialDimension dim : ALL) {
			if (dim.key() == level.dimension()) {
				return dim;
			}
		}
		return null;
	}
}
