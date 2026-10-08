package dev.celestial.eden;

import dev.celestial.registry.ModBlocks;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.levelgen.Heightmap;

/** Утром (по часам Верхнего мира) около игроков в Раю выпадает роса-манна на золотую траву; днём она тает сама (MannaDewBlock). */
public final class Manna {
	private Manna() {}

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 80 != 0) {
				return;
			}
			for (ServerPlayer p : server.getPlayerList().getPlayers()) {
				if (p.level() instanceof ServerLevel level && level.dimension().identifier().getPath().equals("heaven")) {
					fall(level, p);
				}
			}
		});
	}

	static boolean dawn(ServerLevel level) {
		long time = level.getOverworldClockTime() % 24000L;
		return time >= 23000L || time < 3000L;
	}

	public static void fall(ServerLevel level, ServerPlayer player) {
		if (!dawn(level)) {
			return;
		}
		for (int i = 0; i < 6; i++) {
			int x = player.getBlockX() + level.getRandom().nextInt(41) - 20;
			int z = player.getBlockZ() + level.getRandom().nextInt(41) - 20;
			int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
			BlockPos pos = new BlockPos(x, y, z);
			if (Math.abs(y - player.getBlockY()) < 24 && level.getBlockState(pos).isAir() && level.getBlockState(pos.below()).is(ModBlocks.GOLDEN_GRASS)) {
				level.setBlock(pos, ModBlocks.MANNA_DEW.defaultBlockState(), 3);
			}
		}
	}
}
