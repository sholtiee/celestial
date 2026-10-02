package dev.celestial.client.grace;

import dev.celestial.Celestial;
import dev.celestial.data.CelestialData;
import dev.celestial.data.PlayerData;
import dev.celestial.grace.Grace;
import dev.celestial.grace.GracePayloads;
import dev.celestial.grace.Skill;
import dev.celestial.grace.Spell;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.phys.Vec3;

/** Клиент Благодати: клавиши, HUD Сияния, двойной прыжок и рывок (движение игрока считается на клиенте). */
public final class GraceClient {
	private static final KeyMapping.Category CATEGORY = new KeyMapping.Category(Celestial.id("celestial"));
	// коды клавиш в 26.3 — скан-коды SDL: V=25, B=5, G=10, K=14
	public static final KeyMapping CAST = KeyMappingHelper.registerKeyMapping(new KeyMapping("key.celestial.cast", 25, CATEGORY));
	public static final KeyMapping CYCLE = KeyMappingHelper.registerKeyMapping(new KeyMapping("key.celestial.cycle_spell", 5, CATEGORY));
	public static final KeyMapping DASH = KeyMappingHelper.registerKeyMapping(new KeyMapping("key.celestial.dash", 10, CATEGORY));
	public static final KeyMapping CODEX = KeyMappingHelper.registerKeyMapping(new KeyMapping("key.celestial.codex", 14, CATEGORY));

	private static int selected;
	private static boolean jumpWasDown;
	private static boolean doubleJumpUsed;
	private static int dashCooldown;

	private GraceClient() {}

	public static PlayerData data() {
		LocalPlayer player = Minecraft.getInstance().player;
		return player == null ? PlayerData.EMPTY : player.getAttachedOrElse(CelestialData.PLAYER, PlayerData.EMPTY);
	}

	public static List<Spell> available() {
		PlayerData d = data();
		List<Spell> out = new ArrayList<>();
		for (Spell s : Spell.values()) {
			if (s.requires == null || d.hasSkill(s.requires.id)) {
				out.add(s);
			}
		}
		return out;
	}

	public static Spell selectedSpell() {
		List<Spell> list = available();
		return list.get(Math.floorMod(selected, list.size()));
	}

	public static void init() {
		ClientTickEvents.END_CLIENT_TICK.register(GraceClient::tick);
		HudElementRegistry.attachElementAfter(VanillaHudElements.HOTBAR, Celestial.id("radiance"), (graphics, delta) -> {
			Minecraft mc = Minecraft.getInstance();
			if (mc.player == null || mc.gui.hud.isHidden()) {
				return;
			}
			PlayerData d = data();
			float max = Grace.maxRadiance(d);
			int x = graphics.guiWidth() / 2 + 98;
			int y = graphics.guiHeight() - 12;
			int w = 72;
			graphics.fill(x - 1, y - 1, x + w + 1, y + 5, 0xAA000000);
			graphics.fill(x, y, x + (int) (w * Math.min(1, d.radiance() / max)), y + 4, 0xFFFFE08A);
			Spell s = selectedSpell();
			int color = d.radiance() >= s.cost ? 0xFFFFF3C6 : 0xFF9AA3B5;
			Component name = Component.translatable("spell.celestial." + s.id);
			// название заклинания не должно вылезать за край экрана
			int tx = Math.min(x, graphics.guiWidth() - mc.font.width(name) - 2);
			graphics.text(mc.font, name, tx, y - 10, color);
		});
	}

	private static void tick(Minecraft mc) {
		LocalPlayer player = mc.player;
		if (player == null) {
			return;
		}
		while (CODEX.consumeClick()) {
			mc.gui.setScreen(new CodexScreen());
		}
		while (CYCLE.consumeClick()) {
			selected = Math.floorMod(selected + 1, available().size());
			player.sendOverlayMessage(Component.translatable("spell.celestial." + selectedSpell().id));
		}
		while (CAST.consumeClick()) {
			ClientPlayNetworking.send(new GracePayloads.CastSpell(selectedSpell().ordinal()));
		}
		PlayerData d = data();
		if (dashCooldown > 0) {
			dashCooldown--;
		}
		while (DASH.consumeClick()) {
			if (d.hasSkill(Skill.DASH.id) && dashCooldown == 0) {
				Vec3 look = player.getLookAngle();
				Vec3 m = player.getDeltaMovement();
				player.setDeltaMovement(m.x + look.x * 1.3, Math.max(m.y, 0.15), m.z + look.z * 1.3);
				player.playSound(SoundEvents.BREEZE_JUMP, 0.8F, 1.4F);
				for (int i = 0; i < 10; i++) {
					player.level().addParticle(ParticleTypes.CLOUD, player.getRandomX(0.6), player.getRandomY(), player.getRandomZ(0.6), 0, 0, 0);
				}
				dashCooldown = 40;
			}
		}
		// двойной прыжок: второй прыжок в воздухе (до раскрытия крыльев)
		boolean jump = player.input.keyPresses.jump();
		if (player.onGround() || player.isInWater()) {
			doubleJumpUsed = false;
		} else if (jump && !jumpWasDown && !doubleJumpUsed && !player.isFallFlying() && !player.getAbilities().flying
			&& d.hasSkill(Skill.DOUBLE_JUMP.id) && player.getDeltaMovement().y < 0.2) {
			Vec3 m = player.getDeltaMovement();
			player.setDeltaMovement(m.x, 0.62, m.z);
			player.resetFallDistance();
			doubleJumpUsed = true;
			player.playSound(SoundEvents.ENDER_DRAGON_FLAP, 0.4F, 1.8F);
			for (int i = 0; i < 8; i++) {
				player.level().addParticle(ParticleTypes.CLOUD, player.getRandomX(0.5), player.getY(), player.getRandomZ(0.5), 0, -0.05, 0);
			}
		}
		jumpWasDown = jump;
	}
}
