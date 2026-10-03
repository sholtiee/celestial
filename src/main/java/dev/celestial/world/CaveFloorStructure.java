package dev.celestial.world;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import dev.celestial.Celestial;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.NoiseColumn;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pools.DimensionPadding;
import net.minecraft.world.level.levelgen.structure.pools.JigsawPlacement;
import net.minecraft.world.level.levelgen.structure.pools.StructureTemplatePool;
import net.minecraft.world.level.levelgen.structure.pools.alias.PoolAliasLookup;
import net.minecraft.world.level.levelgen.structure.structures.JigsawStructure;
import net.minecraft.world.level.levelgen.structure.templatesystem.LiquidSettings;

/**
 * Постройка «на полу пещеры» для миров с потолком (Бездна и будущие пещерные измерения): карта высот там указывает
 * на крышу, поэтому ищем пол сами — сверху вниз по столбцу шума первую пустоту над твёрдым блоком с запасом высоты.
 * Дальше всё как у обычной jigsaw-постройки.
 */
public final class CaveFloorStructure extends Structure {
	public static final MapCodec<CaveFloorStructure> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
		settingsCodec(i),
		StructureTemplatePool.CODEC.fieldOf("start_pool").forGetter(s -> s.startPool),
		Codec.INT.fieldOf("min_y").forGetter(s -> s.minY),
		Codec.INT.fieldOf("max_y").forGetter(s -> s.maxY),
		Codec.INT.optionalFieldOf("floor_offset", 0).forGetter(s -> s.floorOffset),
		Codec.INT.optionalFieldOf("clearance", 8).forGetter(s -> s.clearance),
		Codec.intRange(1, 116).optionalFieldOf("max_distance_from_center", 80).forGetter(s -> s.maxDistance)
	).apply(i, CaveFloorStructure::new));
	public static final StructureType<CaveFloorStructure> TYPE = Registry.register(BuiltInRegistries.STRUCTURE_TYPE,
		Celestial.id("cave_floor"), () -> CODEC);

	private final Holder<StructureTemplatePool> startPool;
	private final int minY;
	private final int maxY;
	private final int floorOffset;
	private final int clearance;
	private final int maxDistance;

	public CaveFloorStructure(StructureSettings settings, Holder<StructureTemplatePool> startPool, int minY, int maxY, int floorOffset,
		int clearance, int maxDistance) {
		super(settings);
		this.startPool = startPool;
		this.minY = minY;
		this.maxY = maxY;
		this.floorOffset = floorOffset;
		this.clearance = clearance;
		this.maxDistance = maxDistance;
	}

	public static void init() {
	}

	@Override
	public Optional<GenerationStub> findGenerationPoint(GenerationContext context) {
		ChunkPos chunk = context.chunkPos();
		NoiseColumn column = context.chunkGenerator().getBaseColumn(chunk.getMiddleBlockX(), chunk.getMiddleBlockZ(),
			context.heightAccessor(), context.randomState());
		for (int y = maxY; y > minY; y--) {
			BlockState below = column.getBlock(y - 1);
			if (column.getBlock(y).isAir() && !below.isAir() && hasClearance(column, y)) {
				BlockPos start = new BlockPos(chunk.getMinBlockX(), y + floorOffset, chunk.getMinBlockZ());
				return JigsawPlacement.addPieces(context, startPool, Optional.empty(), 1, start, false, Optional.empty(),
					new JigsawStructure.MaxDistance(maxDistance, 256), PoolAliasLookup.EMPTY, DimensionPadding.ZERO,
					LiquidSettings.IGNORE_WATERLOGGING);
			}
		}
		return Optional.empty();
	}

	private boolean hasClearance(NoiseColumn column, int floor) {
		for (int y = floor; y < floor + clearance; y++) {
			if (!column.getBlock(y).isAir()) {
				return false;
			}
		}
		return true;
	}

	@Override
	public StructureType<?> type() {
		return TYPE;
	}
}
