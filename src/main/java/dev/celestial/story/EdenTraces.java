package dev.celestial.story;

import dev.celestial.Celestial;
import dev.celestial.data.CelestialData;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;

/**
 * Следы Эдема — итог тайной концовки «Имя» (флаг мира {@code eden_traces}): Угасание обращено вспять, и там, где упал свет,
 * в Верхнем мире прорастают сады с молодым Древом Жизни (шаблон {@code celestial:eden_trace/garden}). Каждому игроку — сад рядом
 * сразу, затем ещё по саду раз в {@link #EVERY_DAYS} игровых дней (запись Кодекса {@code eden_trace_day:<день>}).
 */
public final class EdenTraces {
	public static final int EVERY_DAYS = 7;
	private static final int HALF = 11;

	private EdenTraces() {}

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(EdenTraces::tick);
	}

	private static void tick(MinecraftServer server) {
		if (server.getTickCount() % 200 != 0 || !CelestialData.world(server).has("eden_traces")) {
			return;
		}
		ServerLevel overworld = server.overworld();
		long day = overworld.getOverworldClockTime() / 24000L;
		for (ServerPlayer p : overworld.players()) {
			if (p.isSpectator()) {
				continue;
			}
			var d = CelestialData.get(p);
			long last = d.codex().stream().filter(e -> e.startsWith("eden_trace_day:")).mapToLong(e -> Long.parseLong(e.substring(15))).max().orElse(-1L);
			if (last >= 0 && day - last < EVERY_DAYS) {
				continue;
			}
			BlockPos at = grow(overworld, p);
			if (at != null) {
				CelestialData.update(p, dd -> {
					var out = dd;
					for (String e : dd.codex()) {
						if (e.startsWith("eden_trace_day:")) {
							out = out.withoutCodex(e);
						}
					}
					return out.withCodex("eden_trace_day:" + day).withCodex("place:eden_trace");
				});
				Story.EDEN_TRACE.grant(p);
				int dist = (int) Math.sqrt(at.distSqr(p.blockPosition()));
				p.sendSystemMessage(Component.translatable("story.celestial.eden_trace",
					Component.translatable("direction.celestial." + dev.celestial.fading.TelescopeBlock.directionOf(p.blockPosition(), at)), dist));
			}
		}
	}

	/** Найти ровную поляну в 24–48 блоках и вырастить сад; null — не нашлось (попробует через 10 с). */
	public static BlockPos grow(ServerLevel level, ServerPlayer near) {
		var template = level.getServer().getStructureTemplateManager().get(Celestial.id("eden_trace/garden"));
		if (template.isEmpty()) {
			return null;
		}
		var rnd = level.getRandom();
		for (int attempt = 0; attempt < 12; attempt++) {
			double a = rnd.nextDouble() * Math.PI * 2;
			int r = 24 + rnd.nextInt(25);
			int x = near.getBlockX() + (int) (Math.cos(a) * r);
			int z = near.getBlockZ() + (int) (Math.sin(a) * r);
			if (!level.hasChunk(x >> 4, z >> 4)) {
				continue;
			}
			int y = level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z) - 1;
			BlockPos ground = new BlockPos(x, y, z);
			if (!flat(level, ground)) {
				continue;
			}
			BlockPos origin = ground.offset(-HALF, -1, -HALF);
			template.get().placeInWorld(level, origin, origin, new StructurePlaceSettings(), rnd, 2);
			Celestial.LOGGER.info("След Эдема вырос у {}", ground);
			return ground;
		}
		return null;
	}

	/** Поляна: земля (трава/земля) по углам и в центре почти на одной высоте, не вода. */
	private static boolean flat(Level level, BlockPos c) {
		int[][] probes = {{0, 0}, {-8, -8}, {8, -8}, {-8, 8}, {8, 8}};
		for (int[] q : probes) {
			int y = level.getHeight(Heightmap.Types.WORLD_SURFACE, c.getX() + q[0], c.getZ() + q[1]) - 1;
			if (Math.abs(y - c.getY()) > 2) {
				return false;
			}
			var st = level.getBlockState(new BlockPos(c.getX() + q[0], y, c.getZ() + q[1]));
			if (!st.is(BlockTags.DIRT) && !st.is(net.minecraft.world.level.block.Blocks.GRASS_BLOCK)) {
				return false;
			}
		}
		return true;
	}
}
