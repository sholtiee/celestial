package dev.celestial.fading;

import dev.celestial.registry.ModGameRules;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

/** Звездопады: ночами (чаще на высоких стадиях Угасания) рядом с игроками падают метеориты. */
public final class Meteors {
	private Meteors() {}

	static void maybeFall(ServerLevel level, ServerPlayer player, int stage) {
		if (!level.getGameRules().get(ModGameRules.METEORS) || stage <= 0) {
			return;
		}
		if (level.getRandom().nextFloat() < 0.015F + 0.01F * stage) {
			fallNear(level, player);
		}
	}

	/** Метеорит падает в 40–80 блоках от игрока, наискосок с высоты. */
	public static boolean fallNear(ServerLevel level, ServerPlayer player) {
		Vec3 offset = Fading.horizontal(level.getRandom(), 40, 80);
		int x = (int) (player.getX() + offset.x);
		int z = (int) (player.getZ() + offset.z);
		if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
			return false;
		}
		int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
		Vec3 target = new Vec3(x + 0.5, y, z + 0.5);
		Vec3 slant = Fading.horizontal(level.getRandom(), 30, 50);
		Vec3 from = target.add(slant.x, Math.min(level.getMaxY() - y - 4, 110), slant.z);
		if (!level.hasChunkAt(BlockPos.containing(from))) {
			from = target.add(0, Math.min(level.getMaxY() - y - 4, 110), 0);
		}
		Meteor.launch(level, from, target);
		player.sendSystemMessage(Component.translatable("fading.celestial.meteor_seen"));
		level.playSound(null, player.blockPosition(), SoundEvents.FIREWORK_ROCKET_LARGE_BLAST_FAR, SoundSource.AMBIENT, 2.0F, 0.5F);
		return true;
	}
}
