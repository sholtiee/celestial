package dev.celestial.world;

import dev.celestial.Celestial;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.portal.TeleportTransition;
import net.minecraft.world.phys.Vec3;

/** Измерение Рая: ключ, лёгкая гравитация и падение с островов обратно в Верхний мир. */
public final class HeavenDimension {
	public static final ResourceKey<Level> HEAVEN = ResourceKey.create(Registries.DIMENSION, Celestial.id("heaven"));

	/** Ниже этой высоты игрок «выпадает» из Рая. */
	public static final int FALL_OUT_Y = -24;
	/** Высота, с которой игрок появляется в небе Верхнего мира. */
	public static final double OVERWORLD_ARRIVAL_Y = 300.0;

	private static final Identifier GRAVITY_ID = Celestial.id("heaven_gravity");
	private static final Identifier SAFE_FALL_ID = Celestial.id("heaven_safe_fall");
	private static final AttributeModifier GRAVITY = new AttributeModifier(GRAVITY_ID, -0.4, AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
	private static final AttributeModifier SAFE_FALL = new AttributeModifier(SAFE_FALL_ID, 6.0, AttributeModifier.Operation.ADD_VALUE);

	private HeavenDimension() {}

	public static boolean isHeaven(Level level) {
		return level.dimension() == HEAVEN;
	}

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(HeavenDimension::tick);
	}

	private static void tick(MinecraftServer server) {
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			boolean inHeaven = isHeaven(player.level());
			applyHeavenPhysics(player, inHeaven);
			if (inHeaven && player.getY() < FALL_OUT_Y && !player.isSpectator()) {
				fallToOverworld(player, server);
			}
		}
	}

	/** Включает или снимает небесную физику: меньше гравитация, мягче падение. */
	public static void applyHeavenPhysics(LivingEntity entity, boolean enabled) {
		toggle(entity.getAttribute(Attributes.GRAVITY), GRAVITY, enabled);
		toggle(entity.getAttribute(Attributes.SAFE_FALL_DISTANCE), SAFE_FALL, enabled);
	}

	private static void toggle(AttributeInstance attribute, AttributeModifier modifier, boolean enabled) {
		if (attribute == null) {
			return;
		}
		boolean has = attribute.hasModifier(modifier.id());
		if (enabled && !has) {
			attribute.addTransientModifier(modifier);
		} else if (!enabled && has) {
			attribute.removeModifier(modifier.id());
		}
	}

	/** Падение с края Рая: игрок медленно опускается с неба Верхнего мира. */
	private static void fallToOverworld(ServerPlayer player, MinecraftServer server) {
		ServerLevel overworld = server.overworld();
		Vec3 target = new Vec3(player.getX(), OVERWORLD_ARRIVAL_Y, player.getZ());
		player.teleport(new TeleportTransition(overworld, target, Vec3.ZERO, player.getYRot(), player.getXRot(), TeleportTransition.DO_NOTHING));
		player.resetFallDistance();
		player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 20 * 30, 0, false, true));
	}
}
