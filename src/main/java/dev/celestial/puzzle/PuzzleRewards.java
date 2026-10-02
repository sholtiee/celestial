package dev.celestial.puzzle;

import dev.celestial.data.CelestialData;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;

/** Общая награда за решённую загадку: эффект, звук, очко Благодати и запись в Кодекс. */
public final class PuzzleRewards {
	private PuzzleRewards() {}

	public static void solved(ServerLevel level, BlockPos pos, Player player, String kind) {
		level.playSound(null, pos, SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.BLOCKS, 1.0F, 1.2F);
		level.sendParticles(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5, 40, 0.5, 0.6, 0.5, 0.15);
		if (player != null) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.solved"));
			CelestialData.update(player, d -> d.withGrace(d.grace() + 1).withCodex("puzzle_" + kind));
		}
	}
}
