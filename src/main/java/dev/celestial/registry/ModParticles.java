package dev.celestial.registry;

import dev.celestial.Celestial;
import net.fabricmc.fabric.api.particle.v1.FabricParticleTypes;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.BuiltInRegistries;

/** Свои частицы (текстуры — tools/gen_particles.py, поведение — client/render/CelestialParticle). */
public final class ModParticles {
	public static final SimpleParticleType STARLIGHT = register("starlight");
	public static final SimpleParticleType SHADOW = register("shadow");
	public static final SimpleParticleType SPORE = register("spore");
	public static final SimpleParticleType FEATHER = register("feather");
	public static final SimpleParticleType RIFT = register("rift");

	private ModParticles() {}

	private static SimpleParticleType register(String name) {
		return Registry.register(BuiltInRegistries.PARTICLE_TYPE, Celestial.id(name), FabricParticleTypes.simple());
	}

	public static void init() {
	}
}
