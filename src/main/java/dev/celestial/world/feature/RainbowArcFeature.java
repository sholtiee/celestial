package dev.celestial.world.feature;

import com.mojang.serialization.MapCodec;
import java.util.LinkedHashMap;
import java.util.Map;
import net.minecraft.core.Direction;
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
		// сначала собираем форму (шаг 1° и множество — без щелей между полосами), потом проверяем, а не рисуем «что влезет»
		Map<BlockPos, BlockState> shape = new LinkedHashMap<>();
		for (int band = 0; band < BANDS.length; band++) {
			double r = radius - band;
			BlockState glass = BANDS[band].defaultBlockState();
			for (int a = 0; a <= 180; a++) {
				double rad = Math.toRadians(a);
				int u = (int) Math.round(Math.cos(rad) * r);
				int v = (int) Math.round(Math.sin(rad) * r);
				for (int w = 0; w < width; w++) {
					shape.putIfAbsent((alongX ? origin.offset(u, v, w) : origin.offset(w, v, u)).immutable(), glass);
				}
			}
		}
		// арка не должна врезаться: вся форма и её окружение в 1 блок — воздух (иначе — не ставим вовсе, а не обрубок)
		for (BlockPos pos : shape.keySet()) {
			if (!level.getBlockState(pos).isAir()) {
				return false;
			}
			for (Direction d : Direction.values()) {
				BlockPos n = pos.relative(d);
				if (!shape.containsKey(n) && !level.getBlockState(n).isAir()) {
					return false;
				}
			}
		}
		// и хотя бы одна «нога» стоит на земле (в пределах 4 блоков под концом внешней полосы), а не висит в пустоте
		BlockPos footA = alongX ? origin.offset(radius, 0, 1) : origin.offset(1, 0, radius);
		BlockPos footB = alongX ? origin.offset(-radius, 0, 1) : origin.offset(1, 0, -radius);
		if (!hasGroundBelow(level, footA) && !hasGroundBelow(level, footB)) {
			return false;
		}
		shape.forEach((pos, glass) -> level.setBlock(pos, glass, Block.UPDATE_CLIENTS));
		return true;
	}

	private static boolean hasGroundBelow(WorldGenLevel level, BlockPos foot) {
		for (int i = 1; i <= 4; i++) {
			if (!level.getBlockState(foot.below(i)).isAir()) {
				return true;
			}
		}
		return false;
	}
}
