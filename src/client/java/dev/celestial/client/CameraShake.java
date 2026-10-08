package dev.celestial.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.celestial.network.ShakePayload;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.util.Mth;

/** Тряска камеры по пакету сервера; затухает к концу, масштабируется ванильной настройкой «Эффекты искажения». */
public final class CameraShake {
	private static float strength;
	private static int ticks;
	private static int total;

	private CameraShake() {}

	public static void init() {
		ClientPlayNetworking.registerGlobalReceiver(ShakePayload.TYPE, (payload, context) -> {
			// новая тряска не обрывает более сильную текущую
			if (payload.strength() >= current()) {
				strength = payload.strength();
				ticks = total = Math.max(1, payload.ticks());
			}
		});
		ClientTickEvents.END_CLIENT_TICK.register(mc -> {
			if (ticks > 0) {
				ticks--;
			}
		});
	}

	private static float current() {
		return ticks > 0 ? strength * ticks / total : 0.0F;
	}

	/** Вызывается из миксина в GameRenderer.bobHurt: поворачивает взгляд на долю градуса туда-сюда. */
	public static void apply(PoseStack pose) {
		float s = current();
		if (s <= 0.0F) {
			return;
		}
		Minecraft mc = Minecraft.getInstance();
		s *= mc.options.screenEffectScale().get().floatValue();
		if (s <= 0.0F) {
			return;
		}
		float t = (System.nanoTime() % 100_000_000_000L) / 1.0E9F;
		pose.rotateDegrees(Axis.ZP, Mth.sin(t * 47.0F) * s);
		pose.rotateDegrees(Axis.XP, Mth.sin(t * 61.0F + 1.3F) * s * 0.7F);
		pose.rotateDegrees(Axis.YP, Mth.sin(t * 53.0F + 2.1F) * s * 0.5F);
	}
}
