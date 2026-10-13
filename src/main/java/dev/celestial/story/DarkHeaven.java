package dev.celestial.story;

import dev.celestial.data.CelestialData;
import dev.celestial.registry.ModBlocks;
import dev.celestial.registry.ModEntities;
import dev.celestial.world.HeavenDimension;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LeavesBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;

/**
 * Тёмный облик Рая после «Поглотить»: вокруг игроков в Раю расползается порча — золотая трава становится пепельной,
 * кроны вянут, цветы и травы осыпаются, облака темнеют до грозовых. В сумраке выходят Тени. Ангелы отворачиваются (Angel.mobInteract).
 * Порча идёт там, где ходят игроки (как и сам «взятый свет»), — мир не перестраивается целиком.
 */
public final class DarkHeaven {
	private static final int RADIUS = 40, TRIES = 24, SHADOWS = 3;

	private DarkHeaven() {}

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(DarkHeaven::tick);
	}

	public static boolean active(MinecraftServer server) {
		return CelestialData.world(server).has("ending_" + Endings.CONSUME);
	}

	private static void tick(MinecraftServer server) {
		if (server.getTickCount() % 10 != 0 || !active(server)) {
			return;
		}
		ServerLevel heaven = server.getLevel(HeavenDimension.HEAVEN);
		if (heaven == null || heaven.players().isEmpty()) {
			return;
		}
		var random = heaven.getRandom();
		for (ServerPlayer p : heaven.players()) {
			for (int i = 0; i < TRIES; i++) {
				int x = p.getBlockX() + random.nextInt(RADIUS * 2 + 1) - RADIUS;
				int z = p.getBlockZ() + random.nextInt(RADIUS * 2 + 1) - RADIUS;
				if (!heaven.hasChunkAt(new BlockPos(x, p.getBlockY(), z))) {
					continue;
				}
				int top = heaven.getHeight(Heightmap.Types.WORLD_SURFACE, x, z) - 1;
				for (int y = top; y >= top - 4; y--) {
					blight(heaven, new BlockPos(x, y, z));
				}
			}
			if (server.getTickCount() % 200 == 0) {
				spawnShadow(heaven, p);
			}
		}
	}

	private static void blight(ServerLevel level, BlockPos pos) {
		BlockState s = level.getBlockState(pos);
		BlockState to = null;
		if (s.is(ModBlocks.GOLDEN_GRASS)) {
			to = ModBlocks.ASHEN_GRASS.defaultBlockState();
		} else if (s.is(ModBlocks.SKYWOOD_LEAVES) || s.is(ModBlocks.CLOUD_WILLOW_LEAVES)) {
			to = ModBlocks.WITHERED_LEAVES.defaultBlockState().setValue(LeavesBlock.DISTANCE, s.getValue(LeavesBlock.DISTANCE))
				.setValue(LeavesBlock.PERSISTENT, s.getValue(LeavesBlock.PERSISTENT));
		} else if (s.is(ModBlocks.GOLDEN_TUFT) || s.is(ModBlocks.STARFLOWER)) {
			to = Blocks.AIR.defaultBlockState();
		} else if (s.is(ModBlocks.CLOUD) || s.is(ModBlocks.GOLDEN_CLOUD)) {
			to = ModBlocks.RAIN_CLOUD.defaultBlockState();
		}
		if (to != null) {
			level.setBlock(pos, to, Block.UPDATE_CLIENTS);
			if (level.getRandom().nextInt(6) == 0) {
				level.sendParticles(ParticleTypes.SMOKE, pos.getX() + 0.5, pos.getY() + 1.1, pos.getZ() + 0.5, 3, 0.3, 0.1, 0.3, 0.01);
			}
		}
	}

	private static void spawnShadow(ServerLevel level, ServerPlayer p) {
		if (level.getEntitiesOfClass(dev.celestial.fading.Shadow.class, p.getBoundingBox().inflate(48)).size() >= SHADOWS) {
			return;
		}
		var random = level.getRandom();
		double a = random.nextDouble() * Math.PI * 2;
		int x = p.getBlockX() + (int) (Math.cos(a) * (16 + random.nextInt(10)));
		int z = p.getBlockZ() + (int) (Math.sin(a) * (16 + random.nextInt(10)));
		int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
		if (!level.getBlockState(new BlockPos(x, y - 1, z)).is(ModBlocks.ASHEN_GRASS)) {
			return;  // Тени ходят только по уже потемневшей земле
		}
		ModEntities.SHADOW.spawn(level, new BlockPos(x, y, z), EntitySpawnReason.EVENT);
	}
}
