package dev.celestial.client;

import dev.celestial.Celestial;
import dev.celestial.world.dim.AbyssFeatures;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.phys.Vec3;

/**
 * «Плавание» в невесомости Астрала: в воздухе удерживай прыжок — плавный подъём (запас тяги {@link #MAX} тиков, восполняется на опоре),
 * красться — спуск. Движение своего игрока считает клиент, поэтому тяга здесь; гравитацию ×0.15 ставит сервер (DimensionPhysics).
 * Полоска запаса — тонкая черта под прицелом, пока не полна.
 */
public final class AstralSwim {
	public static final int MAX = 60;
	private static final double LIFT = 0.05;
	private static final double MAX_UP = 0.32;
	private static final double SINK = 0.05;
	private static final double MAX_DOWN = -0.5;
	private static int thrust = MAX;

	private AstralSwim() {}

	public static void init() {
		ClientTickEvents.END_CLIENT_TICK.register(AstralSwim::tick);
		HudElementRegistry.attachElementAfter(VanillaHudElements.CROSSHAIR, Celestial.id("astral_thrust"), (g, delta) -> {
			Minecraft mc = Minecraft.getInstance();
			if (mc.player == null || !inSpace(mc.player) || thrust >= MAX) {
				return;
			}
			int w = 40, x = g.guiWidth() / 2 - w / 2, y = g.guiHeight() / 2 + 10;
			g.fill(x - 1, y - 1, x + w + 1, y + 2, 0x88000000);
			g.fill(x, y, x + w * thrust / MAX, y + 1, 0xFFB8C8FF);
		});
	}

	public static boolean inSpace(LocalPlayer p) {
		return p.level().dimension() == AbyssFeatures.ASTRAL;
	}

	private static void tick(Minecraft mc) {
		LocalPlayer p = mc.player;
		if (p == null || !inSpace(p) || p.getAbilities().flying || p.isPassenger() || p.isInWater() || p.isSpectator()) {
			return;
		}
		if (p.onGround()) {
			thrust = MAX;
			return;
		}
		Vec3 m = p.getDeltaMovement();
		if (mc.options.keyJump.isDown() && thrust > 0) {
			thrust--;
			p.setDeltaMovement(m.x, Math.min(m.y + LIFT, MAX_UP), m.z);
		} else if (mc.options.keyShift.isDown()) {
			p.setDeltaMovement(m.x, Math.max(m.y - SINK, MAX_DOWN), m.z);
		}
	}

	/** Для сценариев автопилота и HUD: сколько тяги осталось. */
	public static int thrust() {
		return thrust;
	}
}
