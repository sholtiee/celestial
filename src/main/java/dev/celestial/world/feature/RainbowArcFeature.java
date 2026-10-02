package dev.celestial.world.feature;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.feature.Feature;

/** Радужная арка из цветного стекла: полукруг в небе, по верхней полосе можно пройти. */
public record RainbowArcFeature() implements Feature {
	public static final MapCodec<RainbowArcFeature> CODEC = MapCodec.unit(RainbowArcFeature::new);
	private static final Block[] BANDS = {
		Blocks.STAINED_GLASS.red(), Blocks.STAINED_GLASS.orange(), Blocks.STAINED_GLASS.yellow(),
		Blocks.STAINED_GLASS.lime(), Blocks.STAINED_GLASS.lightBlue(), Blocks.STAINED_GLASS.purple()};

	@Override
	public MapCodec<RainbowArcFeature> codec() {
		return CODEC;
	}

	@Override
	public boolean place(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin) {
		int radius = 7 + random.nextInt(2);
		boolean alongX = random.nextBoolean();
		int width = 3;
		for (int band = 0; band < BANDS.length; band++) {
			double r = radius - band;
			BlockState glass = BANDS[band].defaultBlockState();
			for (int a = 0; a <= 180; a += 2) {
				double rad = Math.toRadians(a);
				int u = (int) Math.round(Math.cos(rad) * r);
				int v = (int) Math.round(Math.sin(rad) * r);
				for (int w = 0; w < width; w++) {
					BlockPos pos = alongX ? origin.offset(u, v, w) : origin.offset(w, v, u);
					if (level.getBlockState(pos).isAir()) {
						level.setBlock(pos, glass, Block.UPDATE_CLIENTS);
					}
				}
			}
		}
		return true;
	}
}
