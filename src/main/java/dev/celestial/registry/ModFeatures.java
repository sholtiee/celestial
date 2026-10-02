package dev.celestial.registry;

import dev.celestial.Celestial;
import dev.celestial.world.feature.RainbowArcFeature;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;

public final class ModFeatures {
	private ModFeatures() {}

	public static void init() {
		Registry.register(BuiltInRegistries.FEATURE_TYPE, Celestial.id("rainbow_arc"), RainbowArcFeature.CODEC);
	}
}
