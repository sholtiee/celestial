package dev.celestial.world;

import dev.celestial.Celestial;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.Level;

/** Ключ измерения Рая. Физика и падение — в {@link dev.celestial.world.dim.DimensionPhysics}. */
public final class HeavenDimension {
	public static final ResourceKey<Level> HEAVEN = ResourceKey.create(Registries.DIMENSION, Celestial.id("heaven"));

	private HeavenDimension() {}

	public static boolean isHeaven(Level level) {
		return level.dimension() == HEAVEN;
	}
}
