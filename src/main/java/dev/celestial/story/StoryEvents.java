package dev.celestial.story;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;

/** Точки сюжета «Угасающий свет». Наполняется на этапе сюжета. */
public final class StoryEvents {
	private StoryEvents() {}

	public static void onHeavenPortalLit(Player player) {
	}

	public static void onSeraphDefeated(ServerLevel level, LivingEntity seraph, DamageSource source) {
	}
}
