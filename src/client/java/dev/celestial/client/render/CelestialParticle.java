package dev.celestial.client.render;

import dev.celestial.registry.ModParticles;
import net.fabricmc.fabric.api.client.particle.v1.ParticleProviderRegistry;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.SimpleAnimatedParticle;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;

/**
 * Частицы Celestial: одна реализация, разные настройки. Звёздные искры мерцают и светятся,
 * клочья тьмы растут и тают, споры парят, перья падают с покачиванием, искры разлома кружат по спирали.
 */
public class CelestialParticle extends SimpleAnimatedParticle {
	private final Kind kind;
	private final float baseSize;
	private final double spinPhase;

	enum Kind { STARLIGHT, SHADOW, SPORE, FEATHER, RIFT }

	CelestialParticle(ClientLevel level, double x, double y, double z, double xa, double ya, double za, SpriteSet sprites, Kind kind) {
		super(level, x, y, z, sprites, 0.0F);
		this.kind = kind;
		this.xd = xa;
		this.yd = ya;
		this.zd = za;
		this.spinPhase = random.nextDouble() * Math.PI * 2;
		switch (kind) {
			case STARLIGHT -> {
				lifetime = 30 + random.nextInt(25);
				quadSize *= 0.6F + random.nextFloat() * 0.5F;
				setFadeColor(0x9FC4FF);
				yd += 0.01;
			}
			case SHADOW -> {
				lifetime = 40 + random.nextInt(30);
				quadSize *= 1.4F + random.nextFloat();
				setColor(0x1A1226);
				friction = 0.96F;
				yd += 0.015;
			}
			case SPORE -> {
				lifetime = 80 + random.nextInt(60);
				quadSize *= 0.35F + random.nextFloat() * 0.25F;
				friction = 0.98F;
			}
			case FEATHER -> {
				lifetime = 120 + random.nextInt(60);
				quadSize *= 0.8F + random.nextFloat() * 0.3F;
				gravity = 0.01F;
				friction = 0.98F;
			}
			case RIFT -> {
				lifetime = 40 + random.nextInt(20);
				quadSize *= 0.5F + random.nextFloat() * 0.3F;
				setFadeColor(0x3A1A6A);
			}
		}
		this.baseSize = quadSize;
		setSpriteFromAge(sprites);
	}

	@Override
	public void tick() {
		super.tick();
		float life = (float) age / lifetime;
		switch (kind) {
			case STARLIGHT -> quadSize = baseSize * (0.7F + 0.3F * Mth.sin(age * 0.6F + (float) spinPhase));  // мерцание
			case SHADOW -> {
				quadSize = baseSize * (0.6F + life * 0.8F);
				setAlpha(0.75F * (1.0F - life));
			}
			case SPORE -> {
				xd += Mth.sin(age * 0.07F + (float) spinPhase) * 0.0015;
				zd += Mth.cos(age * 0.06F + (float) spinPhase) * 0.0015;
				yd = Math.max(yd, -0.005) + 0.0003;
			}
			case FEATHER -> {
				xd = Mth.sin(age * 0.1F + (float) spinPhase) * 0.03;
				zd = Mth.cos(age * 0.08F + (float) spinPhase) * 0.02;
				roll = Mth.sin(age * 0.1F + (float) spinPhase) * 0.6F;
				oRoll = roll;
			}
			case RIFT -> {
				double a = age * 0.25 + spinPhase;
				xd = Math.cos(a) * 0.06;
				zd = Math.sin(a) * 0.06;
				yd = -0.02;
			}
		}
	}

	@Override
	public int getLightCoords(float a) {
		return kind == Kind.SHADOW ? super.getLightCoords(a) & 0xF00000 | 0x40 : 15728880;
	}

	@Override
	public void move(double xa, double ya, double za) {
		setBoundingBox(getBoundingBox().move(xa, ya, za));
		setLocationFromBoundingbox();
	}

	record Provider(SpriteSet sprites, Kind kind) implements ParticleProvider<SimpleParticleType> {
		@Override
		public Particle createParticle(SimpleParticleType options, ClientLevel level, double x, double y, double z, double xa, double ya, double za,
			RandomSource random) {
			return new CelestialParticle(level, x, y, z, xa, ya, za, sprites, kind);
		}
	}

	public static void init() {
		ParticleProviderRegistry r = ParticleProviderRegistry.getInstance();
		r.register(ModParticles.STARLIGHT, sprites -> new Provider(sprites, Kind.STARLIGHT));
		r.register(ModParticles.SHADOW, sprites -> new Provider(sprites, Kind.SHADOW));
		r.register(ModParticles.SPORE, sprites -> new Provider(sprites, Kind.SPORE));
		r.register(ModParticles.FEATHER, sprites -> new Provider(sprites, Kind.FEATHER));
		r.register(ModParticles.RIFT, sprites -> new Provider(sprites, Kind.RIFT));
	}
}
