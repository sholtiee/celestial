package dev.celestial.block.puzzle.echo;

import dev.celestial.puzzle.Attempts;
import dev.celestial.puzzle.PuzzleRewards;
import dev.celestial.puzzle.PuzzleZone;
import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModBlocks;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * «Эхо во тьме». Где-то в зале скрыто ядро (точка, сид от позиции алтаря, все расстояния до камней различны). Камень,
 * если прислушаться, отзывается эхом через 6 + 3·d тиков (d — расстояние до ядра) — звук и вспышка частиц. Бить камни
 * нужно от дальнего к ближнему. На свету (блочный свет у камня ≥ 4) камень молчит: факел, фонарь, светящийся гриб в
 * руке — загадка решается только в темноте. Ошибка → блокировка Attempts и сброс. Зал охраняется (PuzzleZone).
 */
public class EchoAltarBlockEntity extends BlockEntity implements PuzzleZone {
	private static final int RANGE = 12;
	private final List<BlockPos> stones = new ArrayList<>();
	private Vec3 core = Vec3.ZERO;
	private boolean scanned;
	private int progress;
	private int minX, minY, minZ, maxX, maxY, maxZ;
	private record Echo(BlockPos stone, long due) {}
	private final List<Echo> pending = new ArrayList<>();

	public EchoAltarBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.ECHO_ALTAR, pos, state);
	}

	private boolean solved() {
		return getBlockState().getValue(EchoAltarBlock.SOLVED);
	}

	private void scan(ServerLevel level) {
		stones.clear();
		for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-RANGE, -3, -RANGE), worldPosition.offset(RANGE, 4, RANGE))) {
			if (level.getBlockState(p).is(ModBlocks.ECHO_STONE)) {
				stones.add(p.immutable());
			}
		}
		minX = minY = minZ = Integer.MAX_VALUE;
		maxX = maxY = maxZ = Integer.MIN_VALUE;
		for (BlockPos p : stones) {
			minX = Math.min(minX, p.getX());
			minY = Math.min(minY, p.getY());
			minZ = Math.min(minZ, p.getZ());
			maxX = Math.max(maxX, p.getX());
			maxY = Math.max(maxY, p.getY());
			maxZ = Math.max(maxZ, p.getZ());
		}
		// ядро: случайная точка внутри прямоугольника камней, пока все расстояния не разойдутся хотя бы на 1.5 блока
		RandomSource random = RandomSource.create(worldPosition.asLong() ^ 0x4543484FL);
		for (int tries = 0; tries < 64 && !stones.isEmpty(); tries++) {
			core = new Vec3(minX + random.nextDouble() * (maxX - minX + 1), minY + 0.5, minZ + random.nextDouble() * (maxZ - minZ + 1));
			List<Double> d = new ArrayList<>();
			for (BlockPos s : stones) {
				d.add(Vec3.atCenterOf(s).distanceTo(core));
			}
			d.sort(Double::compare);
			boolean distinct = true;
			for (int i = 1; i < d.size(); i++) {
				distinct &= d.get(i) - d.get(i - 1) >= 1.5;
			}
			if (distinct) {
				break;
			}
		}
		scanned = true;
	}

	public boolean owns(ServerLevel level, BlockPos pos) {
		if (!scanned) {
			scan(level);
		}
		return stones.contains(pos);
	}

	@Override
	public boolean guards(BlockPos pos) {
		return scanned && !solved() && !stones.isEmpty() && pos.getX() >= minX - 3 && pos.getX() <= maxX + 3 && pos.getZ() >= minZ - 3
			&& pos.getZ() <= maxZ + 3 && pos.getY() >= minY - 2 && pos.getY() <= maxY + 5;
	}

	/** Порядок ударов: от дальнего к ближнему. */
	private List<BlockPos> order() {
		List<BlockPos> sorted = new ArrayList<>(stones);
		sorted.sort(Comparator.comparingDouble((BlockPos s) -> Vec3.atCenterOf(s).distanceTo(core)).reversed());
		return sorted;
	}

	private static boolean lit(ServerLevel level, BlockPos stone) {
		int light = 0;
		for (Direction d : Direction.values()) {
			light = Math.max(light, level.getBrightness(LightLayer.BLOCK, stone.relative(d)));
		}
		return light >= 4;
	}

	void listen(ServerLevel level, BlockPos stone, Player player) {
		if (lit(level, stone)) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.echo.muted"));
			return;
		}
		double d = Vec3.atCenterOf(stone).distanceTo(core);
		level.playSound(null, stone, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.5F, 1.4F);
		level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, stone.getX() + 0.5, stone.getY() + 1.1, stone.getZ() + 0.5, 6, 0.2, 0.1, 0.2, 0.01);
		pending.add(new Echo(stone, level.getGameTime() + 6 + Math.round(d * 3)));
	}

	void strike(ServerLevel level, BlockPos stone, Player player) {
		if (player.isCreative() || player.isSpectator()) {
			return;
		}
		if (solved()) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.echo.solved"));
			return;
		}
		int locked = Attempts.lockedSeconds(level, worldPosition, player);
		if (locked > 0) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.locked_wait", locked));
			return;
		}
		if (lit(level, stone)) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.echo.muted"));
			return;
		}
		BlockState state = level.getBlockState(stone);
		if (state.getValue(EchoStoneBlock.STRUCK)) {
			return;  // этот камень уже засчитан в текущей попытке
		}
		List<BlockPos> order = order();
		if (order.get(progress).equals(stone)) {
			progress++;
			level.setBlock(stone, state.setValue(EchoStoneBlock.STRUCK, true), Block.UPDATE_ALL);
			level.playSound(null, stone, SoundEvents.BELL_RESONATE, SoundSource.BLOCKS, 1.0F, 0.8F + progress * 0.15F);
			if (progress >= order.size()) {
				level.setBlock(worldPosition, getBlockState().setValue(EchoAltarBlock.SOLVED, true), Block.UPDATE_ALL);
				Attempts.reset(level, worldPosition, player);
				PuzzleRewards.solved(level, worldPosition, player, "echo", 12);  // реликварий в дальнем конце зала
			}
			return;
		}
		progress = 0;
		for (BlockPos s : stones) {
			BlockState st = level.getBlockState(s);
			if (st.is(ModBlocks.ECHO_STONE) && st.getValue(EchoStoneBlock.STRUCK)) {
				level.setBlock(s, st.setValue(EchoStoneBlock.STRUCK, false), Block.UPDATE_ALL);
			}
		}
		Attempts.fail(level, worldPosition, player, Component.translatable("puzzle.celestial.echo.wrong"));
	}

	void tick(ServerLevel level) {
		if (!scanned) {
			scan(level);
		}
		long now = level.getGameTime();
		pending.removeIf(e -> {
			if (e.due() > now) {
				return false;
			}
			BlockPos s = e.stone();
			level.playSound(null, s, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 1.2F, 0.55F);
			level.sendParticles(ParticleTypes.SONIC_BOOM, s.getX() + 0.5, s.getY() + 1.4, s.getZ() + 0.5, 1, 0, 0, 0, 0);
			return true;
		});
	}
}
