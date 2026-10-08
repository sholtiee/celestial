package dev.celestial.block.puzzle.memory;

import dev.celestial.puzzle.Attempts;
import dev.celestial.puzzle.PuzzleRewards;
import dev.celestial.puzzle.PuzzleZone;
import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModBlocks;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * Плиты памяти: алтарь проигрывает маршрут вспышками плит (с нотами), игрок проходит его ногами по порядку. Маршрут — сид от
 * позиции алтаря (у каждого святилища свой), длина 6. Ошибка → плиты исчезают на 2 с (падение в яму), блокировка Attempts,
 * прогресс сброшен. Нерешённое святилище охраняется (PuzzleZone): нельзя строить мосты над ямой и класть свои блоки.
 */
public class MemoryAltarBlockEntity extends BlockEntity implements PuzzleZone {
	private static final int LENGTH = 6;
	private static final int SHOW_GAP = 14;
	private static final int RANGE = 10;
	private final List<BlockPos> plates = new ArrayList<>();
	private boolean scanned;
	private int minX, minY, minZ, maxX, maxY, maxZ;
	private int playIndex = -1;
	private int playClock;
	private int progress;
	private BlockPos last;

	public MemoryAltarBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.MEMORY_ALTAR, pos, state);
	}

	private boolean solved() {
		return getBlockState().getValue(MemoryAltarBlock.SOLVED);
	}

	private void scan(ServerLevel level) {
		plates.clear();
		for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-RANGE, -3, -RANGE), worldPosition.offset(RANGE, 3, RANGE))) {
			if (level.getBlockState(p).is(ModBlocks.MEMORY_PLATE)) {
				plates.add(p.immutable());
			}
		}
		// порядок плит не зависит от поворота постройки: сортируем по расстоянию до алтаря, затем по координатам
		plates.sort(Comparator.<BlockPos>comparingDouble(p -> p.distSqr(worldPosition)).thenComparingInt(BlockPos::getX).thenComparingInt(BlockPos::getZ));
		minX = minY = minZ = Integer.MAX_VALUE;
		maxX = maxY = maxZ = Integer.MIN_VALUE;
		for (BlockPos p : plates) {
			minX = Math.min(minX, p.getX());
			minY = Math.min(minY, p.getY());
			minZ = Math.min(minZ, p.getZ());
			maxX = Math.max(maxX, p.getX());
			maxY = Math.max(maxY, p.getY());
			maxZ = Math.max(maxZ, p.getZ());
		}
		scanned = true;
	}

	/** Маршрут: индексы плит, без повторов подряд. */
	private List<BlockPos> route() {
		RandomSource random = RandomSource.create(worldPosition.asLong() ^ 0x4D454D4F5259L);
		List<BlockPos> out = new ArrayList<>();
		int prev = -1;
		for (int i = 0; i < LENGTH && !plates.isEmpty(); i++) {
			int k;
			do {
				k = random.nextInt(plates.size());
			} while (k == prev && plates.size() > 1);
			out.add(plates.get(k));
			prev = k;
		}
		return out;
	}

	public boolean owns(BlockPos pos) {
		return scanned && plates.contains(pos);
	}

	@Override
	public boolean guards(BlockPos pos) {
		return scanned && !solved() && !plates.isEmpty() && pos.getX() >= minX - 2 && pos.getX() <= maxX + 2 && pos.getZ() >= minZ - 2
			&& pos.getZ() <= maxZ + 2 && pos.getY() >= minY - 6 && pos.getY() <= maxY + 4;
	}

	void tick(ServerLevel level) {
		if (!scanned) {
			scan(level);
		}
		if (playIndex < 0 || playClock++ % SHOW_GAP != 0) {
			return;
		}
		List<BlockPos> route = route();
		if (playIndex >= route.size()) {
			playIndex = -1;
			return;
		}
		BlockPos p = route.get(playIndex);
		BlockState s = level.getBlockState(p);
		if (s.is(ModBlocks.MEMORY_PLATE)) {
			level.setBlock(p, s.setValue(MemoryPlateBlock.GLOW, MemoryPlateBlock.Glow.SHOW), Block.UPDATE_ALL);
			level.scheduleTick(p, s.getBlock(), SHOW_GAP - 3);
		}
		level.playSound(null, p, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.BLOCKS, 1.2F, 0.6F + 0.15F * (plates.indexOf(p) % 8));
		level.sendParticles(ParticleTypes.END_ROD, p.getX() + 0.5, p.getY() + 1.1, p.getZ() + 0.5, 6, 0.2, 0.1, 0.2, 0.01);
		playIndex++;
	}

	void show(ServerLevel level, Player player) {
		if (!scanned) {
			scan(level);
		}
		if (solved()) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.memory.solved"));
			return;
		}
		int locked = Attempts.lockedSeconds(level, worldPosition, player);
		if (locked > 0) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.locked_wait", locked));
			return;
		}
		resetPlates(level);
		progress = 0;
		last = null;
		playIndex = 0;
		playClock = 0;
		player.sendOverlayMessage(Component.translatable("puzzle.celestial.memory.watch"));
	}

	void stepped(ServerLevel level, BlockPos pos, ServerPlayer player) {
		if (solved() || playIndex >= 0 || pos.equals(last)) {
			return;  // показ ещё идёт, стоит на той же плите или уже решено
		}
		last = pos;
		if (Attempts.lockedSeconds(level, worldPosition, player) > 0) {
			return;
		}
		List<BlockPos> route = route();
		if (route.isEmpty()) {
			return;
		}
		if (route.get(progress).equals(pos)) {
			progress++;
			BlockState s = level.getBlockState(pos);
			level.setBlock(pos, s.setValue(MemoryPlateBlock.GLOW, MemoryPlateBlock.Glow.GOOD), Block.UPDATE_ALL);
			level.playSound(null, pos, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.BLOCKS, 1.2F, 0.6F + 0.15F * (plates.indexOf(pos) % 8));
			if (progress >= route.size()) {
				level.setBlock(worldPosition, getBlockState().setValue(MemoryAltarBlock.SOLVED, true), Block.UPDATE_ALL);
				Attempts.reset(level, worldPosition, player);
				PuzzleRewards.solved(level, worldPosition, player, "memory", 8);
			}
			return;
		}
		// ошибка: плиты исчезают — падение в яму; блокировка, прогресс заново
		progress = 0;
		last = null;
		Attempts.fail(level, worldPosition, player, Component.translatable("puzzle.celestial.memory.wrong"));
		for (BlockPos p : plates) {
			BlockState s = level.getBlockState(p);
			if (s.is(ModBlocks.MEMORY_PLATE)) {
				level.setBlock(p, s.setValue(MemoryPlateBlock.GLOW, MemoryPlateBlock.Glow.GONE), Block.UPDATE_ALL);
				level.scheduleTick(p, s.getBlock(), 40);
			}
		}
		level.playSound(null, pos, SoundEvents.GLASS_BREAK, SoundSource.BLOCKS, 1.2F, 0.7F);
	}

	private void resetPlates(ServerLevel level) {
		for (BlockPos p : plates) {
			BlockState s = level.getBlockState(p);
			if (s.is(ModBlocks.MEMORY_PLATE) && s.getValue(MemoryPlateBlock.GLOW) != MemoryPlateBlock.Glow.OFF) {
				level.setBlock(p, s.setValue(MemoryPlateBlock.GLOW, MemoryPlateBlock.Glow.OFF), Block.UPDATE_ALL);
			}
		}
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putInt("Progress", progress);
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		progress = input.getIntOr("Progress", 0);
		scanned = false;
	}
}
