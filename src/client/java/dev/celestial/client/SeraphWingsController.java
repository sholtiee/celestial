package dev.celestial.client;

import dev.celestial.registry.ModItems;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;
import dev.celestial.Celestial;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.phys.Vec3;

/**
 * Крылья Серафима: в планировании нажатие прыжка — взмах (подъём + рывок вперёд).
 * Взмахов ограниченное число, восстанавливаются на земле. Движение игрока считается на клиенте,
 * поэтому взмах обрабатывается здесь же, без пакетов.
 */
public final class SeraphWingsController {
	public static final int BASE_FLAPS = 5;

	/** Выносливость крыльев растёт с навыками Благодати. */
	public static int maxFlaps() {
		var d = dev.celestial.client.grace.GraceClient.data();
		return BASE_FLAPS + (d.hasSkill("stamina_1") ? 2 : 0) + (d.hasSkill("stamina_2") ? 3 : 0);
	}
	private static int flaps = BASE_FLAPS;
	private static boolean jumpWasDown;
	private static int regenTicks;
	private static int showTicks;

	private SeraphWingsController() {}

	public static void init() {
		ClientTickEvents.END_CLIENT_TICK.register(SeraphWingsController::tick);
		HudElementRegistry.attachElementAfter(VanillaHudElements.FOOD_BAR, Celestial.id("wing_stamina"), (graphics, delta) -> {
			Minecraft mc = Minecraft.getInstance();
			if (showTicks <= 0 || mc.player == null) {
				return;
			}
			int x = graphics.guiWidth() / 2 + 10;
			int y = graphics.guiHeight() - 49;
			for (int i = 0; i < maxFlaps(); i++) {
				int color = i < flaps ? 0xFFFFE9A8 : 0x66FFFFFF;
				graphics.fill(x + i * 9, y, x + i * 9 + 7, y + 3, color);
			}
		});
	}

	private static void tick(Minecraft mc) {
		LocalPlayer player = mc.player;
		if (player == null) {
			return;
		}
		boolean wearing = player.getItemBySlot(EquipmentSlot.CHEST).is(ModItems.SERAPH_WINGS);
		boolean jumpDown = player.input.keyPresses.jump();
		if (!wearing) {
			showTicks = 0;
			jumpWasDown = jumpDown;
			return;
		}
		if (player.onGround() || player.isInWater()) {
			if (flaps < maxFlaps() && ++regenTicks >= 10) {
				flaps++;
				regenTicks = 0;
			}
		}
		if (player.isFallFlying()) {
			showTicks = 60;
			if (jumpDown && !jumpWasDown && flaps > 0) {
				flap(player);
			}
		} else if (showTicks > 0 && flaps == maxFlaps()) {
			showTicks--;
		}
		jumpWasDown = jumpDown;
	}

	private static void flap(LocalPlayer player) {
		flaps--;
		Vec3 look = player.getLookAngle();
		Vec3 motion = player.getDeltaMovement();
		player.setDeltaMovement(motion.x + look.x * 0.35, Math.max(motion.y, 0.0) + 0.55, motion.z + look.z * 0.35);
		player.playSound(dev.celestial.registry.ModSounds.WING_FLAP, 1.0F, 1.0F);
		for (int i = 0; i < 8; i++) {
			player.level().addParticle(ParticleTypes.CLOUD, player.getRandomX(1.0), player.getY() + 0.5, player.getRandomZ(1.0), 0, -0.05, 0);
		}
	}
}
