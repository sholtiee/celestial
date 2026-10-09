package dev.celestial.client.memory;

import dev.celestial.Celestial;
import dev.celestial.network.MemoryOverlayPayload;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;
import net.minecraft.client.Minecraft;

/**
 * Плёнка памяти (Отблески, docs/LORE.md §5c): пока странник в воспоминании — тёплая золотая виньетка по краям экрана и лёгкая дымка;
 * при входе и выходе — бело-золотая вспышка; сцена может «приглушить свет» (шаг `dim`). Рисуется и при скрытом HUD:
 * это часть картинки, а не интерфейс.
 */
public final class MemoryOverlay {
	private static final int FLASH = 24;
	private static boolean active;
	private static float dim;
	private static float shownDim;
	private static int flash;

	private MemoryOverlay() {}

	public static void init() {
		ClientPlayNetworking.registerGlobalReceiver(MemoryOverlayPayload.TYPE, (payload, context) -> {
			if (payload.active() != active) {
				flash = FLASH;
			}
			active = payload.active();
			dim = payload.dim();
		});
		ClientTickEvents.END_CLIENT_TICK.register(mc -> {
			if (flash > 0) {
				flash--;
			}
			shownDim += (dim - shownDim) * 0.05F;  // свет меркнет плавно
			if (mc.player == null) {
				active = false;
				dim = shownDim = 0;
			}
		});
		HudElementRegistry.attachElementBefore(VanillaHudElements.HOTBAR, Celestial.id("memory_overlay"), (graphics, delta) -> {
			Minecraft mc = Minecraft.getInstance();
			int w = graphics.guiWidth();
			int h = graphics.guiHeight();
			if (active) {
				graphics.fill(0, 0, w, h, argb(0.10F + shownDim * 0.45F, shownDim > 0.01F ? 0x1A1408 : 0xFFE6A8));
				int band = Math.max(24, h / 5);
				graphics.fillGradient(0, 0, w, band, argb(0.55F, 0xE8B85A), argb(0.0F, 0xE8B85A));
				graphics.fillGradient(0, h - band, w, h, argb(0.0F, 0xE8B85A), argb(0.55F, 0xE8B85A));
				int strips = 14;
				int sw = Math.max(2, band / strips);
				for (int i = 0; i < strips; i++) {  // боковые края: столбики с убывающей прозрачностью
					float a = 0.5F * (1.0F - (float) i / strips);
					graphics.fill(i * sw, 0, (i + 1) * sw, h, argb(a * 0.6F, 0xE8B85A));
					graphics.fill(w - (i + 1) * sw, 0, w - i * sw, h, argb(a * 0.6F, 0xE8B85A));
				}
			}
			if (flash > 0) {
				float k = (float) flash / FLASH;
				graphics.fill(0, 0, w, h, argb(k * k, 0xFFF6DC));
			}
		});
	}

	public static boolean active() {
		return active;
	}

	private static int argb(float alpha, int rgb) {
		int a = Math.max(0, Math.min(255, (int) (alpha * 255)));
		return (a << 24) | (rgb & 0xFFFFFF);
	}
}
