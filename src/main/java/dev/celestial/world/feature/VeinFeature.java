package dev.celestial.world.feature;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.feature.Feature;

/**
 * Рудная жила для миров мода: комок из {@code size} блоков руды, заменяющий только {@code target} вокруг точки.
 * Ванильная руда (OreFeature) ставится, лишь если точка ниже карты высот OCEAN_FLOOR_WG, — в парящих астероидах Астрала
 * и в каньонах Хронограда она почти не срабатывала. Здесь проверки нет: жила там, где есть порода.
 */
public record VeinFeature(BlockState ore, Block target, int size) implements Feature {
	public static final MapCodec<VeinFeature> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
		BlockState.CODEC.fieldOf("ore").forGetter(VeinFeature::ore),
		net.minecraft.core.registries.BuiltInRegistries.BLOCK.byNameCodec().fieldOf("target").forGetter(VeinFeature::target),
		Codec.intRange(1, 32).fieldOf("size").forGetter(VeinFeature::size)
	).apply(i, VeinFeature::new));

	@Override
	public MapCodec<VeinFeature> codec() {
		return CODEC;
	}

	@Override
	public boolean place(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin) {
		if (!level.getBlockState(origin).is(target)) {
			return false;  // точка не в породе — жилы нет
		}
		int placed = 0;
		BlockPos.MutableBlockPos pos = origin.mutable();
		for (int i = 0; i < size * 3 && placed < size; i++) {  // случайное блуждание от точки
			if (level.getBlockState(pos).is(target)) {
				level.setBlock(pos, ore, Block.UPDATE_CLIENTS);
				placed++;
			}
			pos.move(random.nextInt(3) - 1, random.nextInt(3) - 1, random.nextInt(3) - 1);
			if (pos.distManhattan(origin) > 4) {
				pos.set(origin);
			}
		}
		return placed > 0;
	}
}
