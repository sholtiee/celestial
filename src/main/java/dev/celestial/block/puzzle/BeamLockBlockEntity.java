package dev.celestial.block.puzzle;

import dev.celestial.block.light.BeamSourceBlock;
import dev.celestial.block.light.LightReceiverBlock;
import dev.celestial.light.LightBeams;
import dev.celestial.light.LightColor;
import dev.celestial.puzzle.PuzzleRewards;
import dev.celestial.puzzle.PuzzleZone;
import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModBlocks;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
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
 * Замок трёх лучей (Зеркальный лабиринт). Раз в пульс сам прослеживает лучи родных (sealed) источников своего лабиринта и
 * отмечает, какие родные приёмники получили луч своего цвета В ЭТОМ ЖЕ пульсе. Решение — красный, зелёный и синий одновременно:
 * зажечь приёмники по очереди, быстро перекручивая зеркала, не выйдет. Объём лабиринта охраняется ({@link PuzzleZone}).
 */
public class BeamLockBlockEntity extends BlockEntity implements PuzzleZone {
	private static final int SCAN = 20;

	private final List<BlockPos> sources = new ArrayList<>();
	private final List<BlockPos> receivers = new ArrayList<>();
	private boolean scanned;
	private boolean solved;
	private int minX, minY, minZ, maxX, maxY, maxZ;

	public BeamLockBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.BEAM_LOCK, pos, state);
	}

	public boolean solved() {
		return solved;
	}

	/** Найти родные источники, приёмники и границы лабиринта (по древним блокам и вечному льду). */
	private void scan(ServerLevel level) {
		sources.clear();
		receivers.clear();
		minX = minY = minZ = Integer.MAX_VALUE;
		maxX = maxY = maxZ = Integer.MIN_VALUE;
		for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-SCAN, -3, -SCAN), worldPosition.offset(SCAN, 6, SCAN))) {
			BlockState s = level.getBlockState(p);
			boolean part = false;
			if (s.getBlock() instanceof BeamSourceBlock && s.getValue(BeamSourceBlock.SEALED)) {
				sources.add(p.immutable());
				part = true;
			} else if (s.getBlock() instanceof LightReceiverBlock && s.getValue(LightReceiverBlock.SEALED)) {
				receivers.add(p.immutable());
				part = true;
			} else if (s.is(ModBlocks.ANCIENT_MIRROR) || s.is(ModBlocks.ANCIENT_PRISM) || s.is(ModBlocks.RIME_ICE) || s.is(ModBlocks.ANCIENT_RED_FILTER)
				|| s.is(ModBlocks.ANCIENT_GREEN_FILTER) || s.is(ModBlocks.ANCIENT_BLUE_FILTER)) {
				part = true;
			}
			if (part) {
				minX = Math.min(minX, p.getX());
				minY = Math.min(minY, p.getY());
				minZ = Math.min(minZ, p.getZ());
				maxX = Math.max(maxX, p.getX());
				maxY = Math.max(maxY, p.getY());
				maxZ = Math.max(maxZ, p.getZ());
			}
		}
		scanned = true;
		setChanged();
	}

	@Override
	public boolean guards(BlockPos pos) {
		return scanned && !solved && pos.getX() >= minX - 1 && pos.getX() <= maxX + 1 && pos.getZ() >= minZ - 1 && pos.getZ() <= maxZ + 1
			&& pos.getY() >= minY - 1 && pos.getY() <= maxY + 2;
	}

	static void serverTick(net.minecraft.world.level.Level level, BlockPos pos, BlockState state, BeamLockBlockEntity be) {
		if (!(level instanceof ServerLevel server) || be.solved) {
			return;
		}
		if (!be.scanned || be.sources.isEmpty() && level.getGameTime() % 200 == 0) {
			be.scan(server);
		}
		if (level.getGameTime() % LightBeams.PULSE != 0) {
			return;
		}
		Set<LightColor> lit = EnumSet.noneOf(LightColor.class);
		for (BlockPos src : be.sources) {
			BlockState s = level.getBlockState(src);
			if (!(s.getBlock() instanceof BeamSourceBlock source) || !s.getValue(BeamSourceBlock.SEALED) || !source.shouldShine(level, src)) {
				continue;
			}
			LightBeams.trace(level, src, s.getValue(BeamSourceBlock.FACING), LightColor.WHITE, new LightBeams.Visitor() {
				@Override
				public void hit(BlockPos hitPos, BlockState hitState, LightColor color, Direction travel) {
					if (hitState.getBlock() instanceof LightReceiverBlock && hitState.getValue(LightReceiverBlock.SEALED)
						&& be.receivers.contains(hitPos) && hitState.getValue(LightReceiverBlock.COLOR) == color) {
						lit.add(color);
					}
				}
			});
		}
		BlockState shown = state.setValue(BeamLockBlock.RED, lit.contains(LightColor.RED)).setValue(BeamLockBlock.GREEN, lit.contains(LightColor.GREEN))
			.setValue(BeamLockBlock.BLUE, lit.contains(LightColor.BLUE));
		if (shown != state) {
			level.setBlock(pos, shown, Block.UPDATE_CLIENTS);
		}
		if (lit.containsAll(EnumSet.of(LightColor.RED, LightColor.GREEN, LightColor.BLUE))) {
			be.solved = true;
			be.setChanged();
			level.setBlock(pos, shown.setValue(BeamLockBlock.SOLVED, true), Block.UPDATE_ALL);
			server.playSound(null, pos, SoundEvents.BEACON_POWER_SELECT, SoundSource.BLOCKS, 2.0F, 1.3F);
			server.sendParticles(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5, 40, 0.4, 0.8, 0.4, 0.08);
			Player player = server.getNearestPlayer(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, 48, false);
			PuzzleRewards.solved(server, pos, player, "mirror_maze");
		}
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putBoolean("Solved", solved);
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		solved = input.getBooleanOr("Solved", false);
		scanned = false;
	}
}
