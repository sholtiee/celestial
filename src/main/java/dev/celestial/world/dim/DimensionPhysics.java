package dev.celestial.world.dim;

import dev.celestial.Celestial;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.Holder;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.portal.TeleportTransition;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/** Применяет к игрокам физику текущего измерения мода и «выпадение» из него. */
public final class DimensionPhysics {
	private static final Identifier GRAVITY_ID = Celestial.id("dimension_gravity");
	private static final Identifier SAFE_FALL_ID = Celestial.id("dimension_safe_fall");

	private DimensionPhysics() {}

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(DimensionPhysics::tick);
		net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents.AFTER_ENTITY_CHANGE_LEVEL.register(
			(original, moved, from, to) -> onChangeDimension(moved));
	}

	/** Последняя твёрдая опора игрока в невесомом измерении — туда выносит из пустоты. */
	private static final java.util.Map<java.util.UUID, Vec3> SAFE = new java.util.HashMap<>();

	private static void tick(MinecraftServer server) {
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			CelestialDimension dim = CelestialDimensions.of(player.level());
			apply(player, dim);
			if (dim != null && dim.space() && player.onGround() && server.getTickCount() % 10 == 0
				&& !player.level().getBlockState(player.blockPosition().below()).getCollisionShape(player.level(), player.blockPosition().below()).isEmpty()) {
				SAFE.put(player.getUUID(), player.position());
			}
			if (dim != null && dim.fallTarget() != null && player.getY() < dim.fallOutY() && !player.isSpectator()) {
				fallOut(player, server, dim);
			}
		}
		// в невесомости лёгкие все живые, не только игроки (раз в секунду — новым и пришедшим)
		if (server.getTickCount() % 20 == 0) {
			for (CelestialDimension dim : CelestialDimensions.ALL) {
				ServerLevel level = dim.space() ? server.getLevel(dim.key()) : null;
				if (level != null) {
					for (net.minecraft.world.entity.Entity e : level.getAllEntities()) {
						if (e instanceof LivingEntity living && !(e instanceof ServerPlayer)) {
							apply(living, dim);
						}
					}
				}
			}
		}
	}

	/** Сущность, ушедшая из невесомого измерения, снова тяжелеет (игроков пересчитывает tick). */
	public static void onChangeDimension(net.minecraft.world.entity.Entity entity) {
		if (entity instanceof LivingEntity living) {
			apply(living, CelestialDimensions.of(living.level()));
		}
	}

	/** Ставит модификаторы гравитации и безопасного падения под профиль (или снимает, если профиля нет). */
	public static void apply(LivingEntity entity, @Nullable CelestialDimension dim) {
		set(entity.getAttribute(Attributes.GRAVITY), GRAVITY_ID, dim == null ? 0 : dim.gravity(), AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
		set(entity.getAttribute(Attributes.SAFE_FALL_DISTANCE), SAFE_FALL_ID, dim == null ? 0 : dim.safeFall(), AttributeModifier.Operation.ADD_VALUE);
	}

	private static void set(@Nullable AttributeInstance attribute, Identifier id, double amount, AttributeModifier.Operation op) {
		if (attribute == null) {
			return;
		}
		AttributeModifier current = attribute.getModifier(id);
		if (current != null && current.amount() == amount) {
			return;
		}
		if (current != null) {
			attribute.removeModifier(id);
		}
		if (amount != 0) {
			attribute.addTransientModifier(new AttributeModifier(id, amount, op));
		}
	}

	private static void fallOut(ServerPlayer player, MinecraftServer server, CelestialDimension dim) {
		ServerLevel target = server.getLevel(dim.fallTarget());
		if (target == null) {
			return;
		}
		if (dim.space()) {
			// пустота Астрала не убивает: звёздный ветер выносит на последний остров
			Vec3 safe = SAFE.getOrDefault(player.getUUID(), new Vec3(0.5, dim.arrivalY(), 0.5));  // не стоял ни на чём — к центру мира
			player.teleport(new TeleportTransition(target, safe.add(0, 0.5, 0), Vec3.ZERO, player.getYRot(), player.getXRot(), TeleportTransition.DO_NOTHING));
			player.resetFallDistance();
			player.sendOverlayMessage(net.minecraft.network.chat.Component.translatable("dimension.celestial.astral.drift"));
			target.sendParticles(dev.celestial.registry.ModParticles.STARLIGHT, safe.x, safe.y + 1, safe.z, 40, 0.4, 0.8, 0.4, 0.02);
			return;
		}
		Vec3 pos = new Vec3(player.getX(), dim.arrivalY(), player.getZ());
		player.teleport(new TeleportTransition(target, pos, Vec3.ZERO, player.getYRot(), player.getXRot(), TeleportTransition.DO_NOTHING));
		player.resetFallDistance();
		player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 20 * 30, 0, false, true));
	}
}
