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

	public static final List<CelestialDimension> ALL = List.of(HEAVEN, ABYSS);

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
