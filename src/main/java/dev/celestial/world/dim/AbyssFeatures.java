package dev.celestial.world.dim;

import dev.celestial.Celestial;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.Level;

/** Ключи Бездны: само измерение и фича гигантского светогриба (растёт из светогриба от костной муки). */
public final class AbyssFeatures {
	public static final ResourceKey<Level> ABYSS = ResourceKey.create(Registries.DIMENSION, Celestial.id("abyss"));
	public static final ResourceKey<net.minecraft.world.level.levelgen.feature.Feature> HUGE_GLOWSHROOM =
		ResourceKey.create(Registries.FEATURE, Celestial.id("huge_glowshroom"));

	public static final ResourceKey<Level> FROZEN_HALLS = ResourceKey.create(Registries.DIMENSION, Celestial.id("frozen_halls"));

	private AbyssFeatures() {}
}
