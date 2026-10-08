package dev.celestial.entity;

import dev.celestial.data.CelestialData;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * Херувим Восточных врат (Быт. 3:24, Иез. 1): четыре лика, четыре крыла и пламенный меч, который обращается кругом сам. Меч — низкая полоса над полом:
 * его надо перепрыгнуть в такт (паркур-испытание `eden_gate`). Тех, кто несёт много Благодати ({@link #SPARING_SKILLS} навыков), меч не трогает.
 * Угол меча считается по игровому времени, поэтому клиент и сервер видят его в одной фазе.
 */
public class GateCherub extends PathfinderMob {
	/** Длина лезвия в блоках и скорость обращения (рад/тик: оборот за ~90 тиков). */
	public static final double RADIUS = 6.5;
	public static final float ROT = 0.07F;
	private static final double HALF_WIDTH = 0.7;
	private static final double HEIGHT = 0.95;
	public static final int SPARING_SKILLS = 8;
	private final Map<UUID, Long> lastHit = new HashMap<>();

	public GateCherub(EntityType<? extends GateCherub> type, Level level) {
		super(type, level);
		setPersistenceRequired();
		setYRot(0);
		this.yBodyRot = 0;
		this.yHeadRot = 0;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return PathfinderMob.createMobAttributes().add(Attributes.MAX_HEALTH, 200.0).add(Attributes.MOVEMENT_SPEED, 0.0)
			.add(Attributes.KNOCKBACK_RESISTANCE, 1.0);
	}

	/** Угол меча: направление (sin a, cos a) в плоскости XZ от херувима; a = 0 — на юг. */
	public static float angle(Level level, float partial) {
		return (level.getGameTime() + partial) * ROT;
	}

	@Override
	protected void registerGoals() {
	}

	@Override
	public void tick() {
		super.tick();
		setYRot(0);
		this.yBodyRot = 0;
		this.yHeadRot = 0;
		if (level() instanceof ServerLevel server) {
			sweep(server);
		} else if (random.nextInt(2) == 0) {
			float a = angle(level(), 0);
			double r = 1.0 + random.nextDouble() * (RADIUS - 1.0);
			level().addParticle(ParticleTypes.FLAME, getX() + Math.sin(a) * r, getY() + 0.5 + random.nextDouble() * 0.5, getZ() + Math.cos(a) * r, 0, 0.02, 0);
		}
	}

	private void sweep(ServerLevel level) {
		float now = angle(level, 0);
		for (ServerPlayer p : level.getPlayers(pl -> pl.distanceToSqr(this) < (RADIUS + 1) * (RADIUS + 1) && !pl.isCreative() && !pl.isSpectator())) {
			double dx = p.getX() - getX();
			double dz = p.getZ() - getZ();
			double r = Math.hypot(dx, dz);
			if (r < 1.2 || r > RADIUS + 0.5 || p.getY() - getY() > HEIGHT || p.getY() - getY() < -1.5) {
				continue;
			}
			// игрок попадает под лезвие, если его угол лежит в полосе, которую меч прошёл за этот тик (и ширине лезвия)
			double delta = wrap(Math.atan2(dx, dz) - now);
			double half = Math.atan2(HALF_WIDTH, r);
			if (delta > half || delta < -(half + ROT)) {
				continue;
			}
			long t = level.getGameTime();
			if (t - lastHit.getOrDefault(p.getUUID(), -100L) < 20) {
				continue;
			}
			lastHit.put(p.getUUID(), t);
			if (CelestialData.get(p).skills().size() >= SPARING_SKILLS) {
				p.sendOverlayMessage(Component.translatable("entity.celestial.gate_cherub.spared"));
				level.sendParticles(ParticleTypes.END_ROD, p.getX(), p.getY() + 1, p.getZ(), 12, 0.3, 0.5, 0.3, 0.02);
				continue;
			}
			p.hurtServer(level, damageSources().magic(), 4.0F);
			Vec3 away = new Vec3(dx, 0, dz).normalize();
			p.setDeltaMovement(away.x * 0.9, 0.45, away.z * 0.9);
			p.needsSync = true;
			level.playSound(null, p.blockPosition(), SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 1.0F, 0.8F);
			level.sendParticles(ParticleTypes.FLAME, p.getX(), p.getY() + 0.5, p.getZ(), 20, 0.3, 0.3, 0.3, 0.05);
			p.sendOverlayMessage(Component.translatable("entity.celestial.gate_cherub.hit"));
		}
		lastHit.keySet().removeIf(id -> level.getPlayerByUUID(id) == null);
	}

	private static double wrap(double a) {
		while (a > Math.PI) {
			a -= Math.PI * 2;
		}
		while (a < -Math.PI) {
			a += Math.PI * 2;
		}
		return a;
	}

	@Override
	protected InteractionResult mobInteract(Player player, InteractionHand hand) {
		if (player instanceof ServerPlayer sp && hand == InteractionHand.MAIN_HAND) {
			sp.sendSystemMessage(Component.translatable("entity.celestial.gate_cherub.line"));
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		return source.is(net.minecraft.tags.DamageTypeTags.BYPASSES_INVULNERABILITY) && super.hurtServer(level, source, amount);
	}

	@Override
	public boolean isPushable() {
		return false;
	}

	@Override
	public boolean removeWhenFarAway(double distSqr) {
		return false;
	}

	@Override
	public boolean causeFallDamage(double fallDistance, float multiplier, DamageSource source) {
		return false;
	}
}
