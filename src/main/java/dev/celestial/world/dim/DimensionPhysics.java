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
	}

	private static void tick(MinecraftServer server) {
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			CelestialDimension dim = CelestialDimensions.of(player.level());
			apply(player, dim);
			if (dim != null && dim.fallTarget() != null && player.getY() < dim.fallOutY() && !player.isSpectator()) {
				fallOut(player, server, dim);
			}
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
		Vec3 pos = new Vec3(player.getX(), dim.arrivalY(), player.getZ());
		player.teleport(new TeleportTransition(target, pos, Vec3.ZERO, player.getYRot(), player.getXRot(), TeleportTransition.DO_NOTHING));
		player.resetFallDistance();
		player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 20 * 30, 0, false, true));
	}
}
