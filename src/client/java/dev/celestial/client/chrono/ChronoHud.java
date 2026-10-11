package dev.celestial.client.chrono;

import dev.celestial.Celestial;
import dev.celestial.chrono.TimeFlow;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.network.chat.Component;

/**
 * Циферблат хода времени: в левом верхнем углу, пока странник в зоне иного времени. Стрелка бежит с масштабом хода
 * (стоит, ползёт, мчится); края экрана слегка тонируются: остановка — холодная серость, ускорение — тёплая латунь.
 */
public final class ChronoHud {
	private static float hand;
	private static float shown = 1.0F;
	private static float fade;

	private ChronoHud() {}

	public static void init() {
		ClientTickEvents.END_CLIENT_TICK.register(mc -> {
			if (mc.player == null || mc.isPaused()) {
				return;
			}
			float s = TimeFlow.scale(mc.player);
			shown += (s - shown) * 0.25F;
			fade += ((Math.abs(s - 1.0F) > 0.01F ? 1.0F : 0.0F) - fade) * 0.15F;
			hand += 0.21F * shown;  // обычный ход — оборот за ~30 тиков
		});
		HudElementRegistry.attachElementAfter(VanillaHudElements.HOTBAR, Celestial.id("chrono_dial"), ChronoHud::draw);
	}

	private static void draw(GuiGraphicsExtractor g, net.minecraft.client.DeltaTracker delta) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.player == null || fade < 0.02F) {
			return;
		}
		int w = g.guiWidth(), h = g.guiHeight();
		float s = TimeFlow.scale(mc.player);
		int tint = s < 0.01F ? 0x8FA3C8 : s < 1.0F ? 0x6F7FB8 : 0xE0A050;
		float edge = (s < 0.01F ? 0.35F : 0.18F) * fade;
		int band = Math.max(12, h / 10);
		g.fillGradient(0, 0, w, band, argb(edge, tint), argb(0, tint));
		g.fillGradient(0, h - band, w, h, argb(0, tint), argb(edge, tint));

		// циферблат
		int r = 10;
		int cx = 8 + r;  // левый верхний угол: справа от хотбара — подпись заклинания, сверху по центру — полоса босса
		int cy = 8 + r;
		int a = (int) (fade * 255) << 24;
		disc(g, cx, cy, r + 1, a | 0x1A1408);
		disc(g, cx, cy, r, a | 0xE9DDB8);
		for (int i = 0; i < 12; i++) {  // риски часов
			double t = i * Math.PI / 6;
			int x = cx + (int) Math.round(Math.sin(t) * (r - 2));
			int y = cy - (int) Math.round(Math.cos(t) * (r - 2));
			g.fill(x, y, x + 1, y + 1, a | (i % 3 == 0 ? 0x5A3A10 : 0x9A8060));
		}
		float partial = delta.getGameTimeDeltaPartialTick(true);
		double ang = (hand + 0.21F * shown * partial) % (Math.PI * 2);
		for (int k = 0; k <= r - 3; k++) {  // стрелка
			int x = cx + (int) Math.round(Math.sin(ang) * k);
			int y = cy - (int) Math.round(Math.cos(ang) * k);
			g.fill(x, y, x + 1, y + 1, a | 0x7A1A10);
		}
		g.fill(cx, cy, cx + 1, cy + 1, a | 0x2A1A08);
		String key = s < 0.01F ? "stopped" : s < 1.0F ? "slow" : "fast";
		Component label = Component.translatable("hud.celestial.time." + key);
		g.text(mc.font, label, cx + r + 4, cy - 4, a | (s < 1.0F ? 0xB8C8F0 : 0xFFD890));
	}

	private static void disc(GuiGraphicsExtractor g, int cx, int cy, int r, int color) {
		for (int dy = -r; dy <= r; dy++) {
			int dx = (int) Math.floor(Math.sqrt(r * r - dy * dy + 0.5));
			g.fill(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, color);
		}
	}

	private static int argb(float alpha, int rgb) {
		int a = Math.max(0, Math.min(255, (int) (alpha * 255)));
		return (a << 24) | (rgb & 0xFFFFFF);
	}
}
