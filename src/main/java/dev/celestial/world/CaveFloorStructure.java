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
 * Постройка «на полу»: для миров с потолком (Бездна, Ад), где карта высот указывает на крышу, и для островов Энда.
 * Пол ищем сами — сверху вниз по столбцу шума первую пустоту над твёрдым блоком с запасом высоты (clearance), причём
 * в пяти точках площади постройки (footprint × footprint от угла чанка: углы и центр). Если хоть в одной точке пола нет
 * (пустота Энда) или перепад больше max_step, чанк пропускается — постройка не висит и не врастает в стену (BUG-052/053).
 */
public final class CaveFloorStructure extends Structure {
	public static final MapCodec<CaveFloorStructure> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
		settingsCodec(i),
		StructureTemplatePool.CODEC.fieldOf("start_pool").forGetter(s -> s.startPool),
		Codec.INT.fieldOf("min_y").forGetter(s -> s.minY),
		Codec.INT.fieldOf("max_y").forGetter(s -> s.maxY),
		Codec.INT.optionalFieldOf("floor_offset", 0).forGetter(s -> s.floorOffset),
		Codec.INT.optionalFieldOf("clearance", 8).forGetter(s -> s.clearance),
		Codec.intRange(1, 116).optionalFieldOf("max_distance_from_center", 80).forGetter(s -> s.maxDistance),
		Codec.intRange(1, 64).optionalFieldOf("footprint", 1).forGetter(s -> s.footprint),
		Codec.intRange(0, 64).optionalFieldOf("max_step", 64).forGetter(s -> s.maxStep)
	).apply(i, CaveFloorStructure::new));
	public static final StructureType<CaveFloorStructure> TYPE = Registry.register(BuiltInRegistries.STRUCTURE_TYPE,
		Celestial.id("cave_floor"), () -> CODEC);

	private final Holder<StructureTemplatePool> startPool;
	private final int minY;
	private final int maxY;
	private final int floorOffset;
	private final int clearance;
	private final int maxDistance;
	private final int footprint;
	private final int maxStep;

	public CaveFloorStructure(StructureSettings settings, Holder<StructureTemplatePool> startPool, int minY, int maxY, int floorOffset,
		int clearance, int maxDistance, int footprint, int maxStep) {
		super(settings);
		this.startPool = startPool;
		this.minY = minY;
		this.maxY = maxY;
		this.floorOffset = floorOffset;
		this.clearance = clearance;
		this.maxDistance = maxDistance;
		this.footprint = footprint;
		this.maxStep = maxStep;
	}

	public static void init() {
	}

	@Override
	public Optional<GenerationStub> findGenerationPoint(GenerationContext context) {
		ChunkPos chunk = context.chunkPos();
		int x0 = chunk.getMinBlockX(), z0 = chunk.getMinBlockZ(), f = footprint - 1;
		int[][] points = footprint <= 1 ? new int[][] {{chunk.getMiddleBlockX(), chunk.getMiddleBlockZ()}}
			: new int[][] {{x0 + f / 2, z0 + f / 2}, {x0, z0}, {x0 + f, z0}, {x0, z0 + f}, {x0 + f, z0 + f}};
		int low = Integer.MAX_VALUE, high = Integer.MIN_VALUE;
		for (int[] p : points) {
			int floor = floorAt(context, p[0], p[1], maxY);
			if (floor < 0) {
				return Optional.empty();  // в этой точке пола нет (пустота) — здесь не строим
			}
			low = Math.min(low, floor);
			high = Math.max(high, floor);
		}
		if (high - low > maxStep) {
			return Optional.empty();
		}
		BlockPos start = new BlockPos(x0, high + floorOffset, z0);
		return JigsawPlacement.addPieces(context, startPool, Optional.empty(), 1, start, false, Optional.empty(),
			new JigsawStructure.MaxDistance(maxDistance, 256), PoolAliasLookup.EMPTY, DimensionPadding.ZERO,
			LiquidSettings.IGNORE_WATERLOGGING);
	}

	/** Высота пола в столбце (первая пустота над твёрдым сверху вниз, с запасом высоты) или −1. */
	private int floorAt(GenerationContext context, int x, int z, int top) {
		NoiseColumn column = context.chunkGenerator().getBaseColumn(x, z, context.heightAccessor(), context.randomState());
		for (int y = top; y > minY; y--) {
			if (column.getBlock(y).isAir() && !column.getBlock(y - 1).isAir() && hasClearance(column, y)) {
				return y;
			}
		}
		return -1;
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
