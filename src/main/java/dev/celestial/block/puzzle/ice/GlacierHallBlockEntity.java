package dev.celestial.block.puzzle.ice;

import dev.celestial.puzzle.PuzzleRewards;
import dev.celestial.puzzle.PuzzleZone;
import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModBlocks;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * Зал скользящего льда, хранится в Ледяном колоколе. Пол зала — связная область ледяных плит и гнёзд рядом с колоколом
 * (определяется сам, поэтому поворот постройки ему не страшен). Первый осмотр запоминает стартовый расклад глыб —
 * колокол возвращает к нему, так что зайти в тупик нельзя. Все гнёзда заняты глыбами → загадка решена.
 */
public class GlacierHallBlockEntity extends BlockEntity implements PuzzleZone {
	private static final int MAX_CELLS = 600;
	/** Своя печать — в нише у колокола; соседние залы цитадели дальше. */
	private static final int DOOR_RADIUS = 6;

	private final List<BlockPos> start = new ArrayList<>();
	private boolean scanned;
	private boolean solved;
	private int floorY;
	private int minX, minZ, maxX, maxZ;
	/** Клетки над полом (где стоят глыбы); не сохраняются, пересчитываются при надобности. */
	private Set<BlockPos> cells;

	public GlacierHallBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.GLACIER_HALL, pos, state);
	}

	public boolean solved() {
		return solved;
	}

	static boolean isFloor(BlockState state) {
		return state.is(ModBlocks.GLACIER_TILE) || state.is(ModBlocks.GLACIER_NEST);
	}

	/** Найти пол зала у колокола и (один раз) запомнить стартовый расклад. */
	private Set<BlockPos> cells(ServerLevel level) {
		if (cells != null) {
			return cells;
		}
		BlockPos seed = null;
		search:
		for (int dy = 0; dy >= -3; dy--) {
			for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-2, dy, -2), worldPosition.offset(2, dy, 2))) {
				if (isFloor(level.getBlockState(p))) {
					seed = p.immutable();
					break search;
				}
			}
		}
		Set<BlockPos> result = new HashSet<>();
		if (seed != null) {
			Deque<BlockPos> queue = new ArrayDeque<>();
			Set<BlockPos> seen = new HashSet<>();
			queue.add(seed);
			while (!queue.isEmpty() && result.size() < MAX_CELLS) {
				BlockPos p = queue.poll();
				if (!seen.add(p) || !isFloor(level.getBlockState(p))) {
					continue;
				}
				result.add(p.above());
				for (Direction d : Direction.Plane.HORIZONTAL) {
					queue.add(p.relative(d));
				}
			}
			floorY = seed.getY();
		}
		cells = result;
		if (!scanned && !result.isEmpty()) {
			scanned = true;
			minX = minZ = Integer.MAX_VALUE;
			maxX = maxZ = Integer.MIN_VALUE;
			for (BlockPos c : result) {
				minX = Math.min(minX, c.getX());
				maxX = Math.max(maxX, c.getX());
				minZ = Math.min(minZ, c.getZ());
				maxZ = Math.max(maxZ, c.getZ());
				if (level.getBlockState(c).is(ModBlocks.GLACIER_RUNE)) {
					start.add(c);
				}
			}
			setChanged();
		}
		return result;
	}

	void ensureScanned(ServerLevel level) {
		if (cells == null) {
			cells(level);
		}
	}

	public boolean contains(ServerLevel level, BlockPos pos) {
		return cells(level).contains(pos);
	}

	@Override
	public boolean guards(BlockPos pos) {
		return scanned && !solved && pos.getX() >= minX - 1 && pos.getX() <= maxX + 1 && pos.getZ() >= minZ - 1 && pos.getZ() <= maxZ + 1
			&& pos.getY() >= floorY && pos.getY() <= floorY + 4;
	}

	/** Толкнуть глыбу в направлении dir. Игрок должен стоять вплотную с противоположной стороны. */
	public void push(ServerLevel level, BlockPos glacier, Direction dir, Player player) {
		Set<BlockPos> region = cells(level);
		if (solved) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.glacier.solved"));
			return;
		}
		if (GlacierSlides.busy(this)) {
			return;
		}
		BlockPos stand = glacier.relative(dir.getOpposite());
		if (player.isPassenger() || player.getBlockY() != glacier.getY() || player.getBlockX() != stand.getX() || player.getBlockZ() != stand.getZ()) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.glacier.stand"));
			return;
		}
		BlockPos to = glacier;
		while (true) {
			BlockPos next = to.relative(dir);
			if (!region.contains(next) || stops(level.getBlockState(next))) {
				break;
			}
			to = next;
		}
		if (to.equals(glacier)) {
			level.playSound(null, glacier, SoundEvents.GLASS_HIT, SoundSource.BLOCKS, 0.8F, 1.6F);
			return;
		}
		GlacierSlides.start(level, glacier, to, dir, this, player);
	}

	/** Глыбу останавливают только части зала: другие глыбы и ледяные колонны. Всё прочее она сметает. */
	private static boolean stops(BlockState state) {
		return state.is(ModBlocks.GLACIER_RUNE) || state.is(ModBlocks.GLACIER_PILLAR) || state.is(ModBlocks.ICE_BELL);
	}

	void afterMove(ServerLevel level, Player player) {
		boolean all = updateNests(level);
		if (all && !solved) {
			solved = true;
			setChanged();
			level.playSound(null, worldPosition, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 2.0F, 0.7F);
			for (BlockPos c : cells(level)) {
				if (level.getBlockState(c.below()).is(ModBlocks.GLACIER_NEST)) {
					level.sendParticles(ParticleTypes.END_ROD, c.getX() + 0.5, c.getY() + 1.2, c.getZ() + 0.5, 16, 0.3, 0.6, 0.3, 0.05);
				}
			}
			PuzzleRewards.solved(level, worldPosition, player, "glacier", DOOR_RADIUS);
		}
	}

	/** Зажечь гнёзда, на которых стоят глыбы. Вернёт true, если заняты все. */
	private boolean updateNests(ServerLevel level) {
		boolean all = true;
		int nests = 0;
		for (BlockPos c : cells(level)) {
			BlockPos below = c.below();
			BlockState floor = level.getBlockState(below);
			if (!floor.is(ModBlocks.GLACIER_NEST)) {
				continue;
			}
			nests++;
			boolean occupied = level.getBlockState(c).is(ModBlocks.GLACIER_RUNE);
			all &= occupied;
			if (floor.getValue(GlacierNestBlock.OCCUPIED) != occupied) {
				level.setBlock(below, floor.setValue(GlacierNestBlock.OCCUPIED, occupied), Block.UPDATE_ALL);
				if (occupied) {
					level.playSound(null, below, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.5F, 1.2F);
				}
			}
		}
		return all && nests > 0;
	}

	/** Ледяной колокол: вернуть глыбы на стартовые места. */
	public void ring(ServerLevel level, Player player) {
		Set<BlockPos> region = cells(level);
		level.playSound(null, worldPosition, SoundEvents.BELL_BLOCK, SoundSource.BLOCKS, 1.5F, 1.6F);
		if (solved) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.glacier.solved"));
			return;
		}
		if (GlacierSlides.busy(this) || start.isEmpty()) {
			return;
		}
		BlockState rune = ModBlocks.GLACIER_RUNE.defaultBlockState();
		for (BlockPos c : region) {
			if (level.getBlockState(c).is(ModBlocks.GLACIER_RUNE) && !start.contains(c)) {
				level.setBlock(c, net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
				level.sendParticles(ParticleTypes.SNOWFLAKE, c.getX() + 0.5, c.getY() + 0.5, c.getZ() + 0.5, 10, 0.3, 0.3, 0.3, 0.02);
			}
		}
		for (BlockPos s : start) {
			if (!level.getBlockState(s).is(ModBlocks.GLACIER_RUNE)) {
				if (!level.getBlockState(s).isAir()) {
					level.destroyBlock(s, true);
				}
				level.setBlock(s, rune, Block.UPDATE_ALL);
				level.sendParticles(ParticleTypes.SNOWFLAKE, s.getX() + 0.5, s.getY() + 0.5, s.getZ() + 0.5, 10, 0.3, 0.3, 0.3, 0.02);
			}
		}
		updateNests(level);
		player.sendOverlayMessage(Component.translatable("puzzle.celestial.glacier.reset"));
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putBoolean("Scanned", scanned);
		output.putBoolean("Solved", solved);
		output.putInt("FloorY", floorY);
		output.putIntArray("Bounds", new int[] {minX, minZ, maxX, maxZ});
		output.store("Start", BlockPos.CODEC.listOf(), start);
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		scanned = input.getBooleanOr("Scanned", false);
		solved = input.getBooleanOr("Solved", false);
		floorY = input.getIntOr("FloorY", 0);
		int[] b = input.getIntArray("Bounds").orElse(new int[4]);
		if (b.length == 4) {
			minX = b[0];
			minZ = b[1];
			maxX = b[2];
			maxZ = b[3];
		}
		start.clear();
		start.addAll(input.read("Start", BlockPos.CODEC.listOf()).orElse(List.of()));
		cells = null;
	}
}
