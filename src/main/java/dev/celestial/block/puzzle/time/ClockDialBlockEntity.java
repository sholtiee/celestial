package dev.celestial.block.puzzle.time;

import dev.celestial.puzzle.PuzzleRewards;
import dev.celestial.puzzle.PuzzleZone;
import dev.celestial.registry.ModBlockEntities;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import net.minecraft.core.BlockPos;
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
 * Состояние циферблата: номер в круге сцепления ({@code Index}), час с фрески ({@code Target}), решено ли.
 * Циферблат с {@code Index} < 0 — неподвижная фреска над настоящим: показывает нужный час, в круг не входит.
 * Круг собирается из всех циферблатов в радиусе 24: поворот циферблата i двигает и циферблат (i+1) mod n.
 */
public class ClockDialBlockEntity extends BlockEntity implements PuzzleZone {
	private static final int RANGE = 24;
	private int index;
	private int target;
	private boolean solved;

	public ClockDialBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.CLOCK_DIAL, pos, state);
	}

	private List<ClockDialBlockEntity> ring(ServerLevel level) {
		List<ClockDialBlockEntity> out = new ArrayList<>();
		for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-RANGE, -4, -RANGE), worldPosition.offset(RANGE, 4, RANGE))) {
			if (level.getBlockEntity(p) instanceof ClockDialBlockEntity d && d.index >= 0) {  // index < 0 — фреска-подсказка
				out.add(d);
			}
		}
		out.sort(Comparator.comparingInt(d -> d.index));
		return out;
	}

	private int hour() {
		return getBlockState().getValue(ClockDialBlock.HOUR);
	}

	private void step(ServerLevel level, int dir) {
		int h = Math.floorMod(hour() + dir, 12);
		level.setBlock(worldPosition, getBlockState().setValue(ClockDialBlock.HOUR, h), Block.UPDATE_ALL);
	}

	void turn(ServerLevel level, Player player, int dir) {
		if (player.isSpectator()) {
			return;
		}
		if (index < 0) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.clock_dials.fresco"));
			return;
		}
		if (solved) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.clock_dials.solved"));
			return;
		}
		List<ClockDialBlockEntity> ring = ring(level);
		int at = ring.indexOf(this);
		step(level, dir);
		level.playSound(null, worldPosition, dev.celestial.registry.ModSounds.CLOCK_TICK, SoundSource.BLOCKS, 1.0F, 1.2F);
		if (ring.size() > 1 && at >= 0) {
			ClockDialBlockEntity next = ring.get((at + 1) % ring.size());
			next.step(level, dir);  // шестерня тянет соседа
			level.playSound(null, next.worldPosition, dev.celestial.registry.ModSounds.GEAR_WHIR, SoundSource.BLOCKS, 0.6F, 1.2F);
			level.sendParticles(ParticleTypes.WAX_ON, next.worldPosition.getX() + 0.5, next.worldPosition.getY() + 0.5, next.worldPosition.getZ() + 0.5,
				4, 0.3, 0.3, 0.3, 0.0);
		}
		if (!player.isCreative() && ring.stream().allMatch(d -> d.hour() == d.target)) {
			for (ClockDialBlockEntity d : ring) {
				d.solved = true;
				d.setChanged();
			}
			level.playSound(null, worldPosition, SoundEvents.BELL_BLOCK, SoundSource.BLOCKS, 2.0F, 0.8F);
			PuzzleRewards.solved(level, worldPosition, player, "clock_dials", 18);  // ниша реликвария — у противоположной стены зала
		}
	}

	@Override
	public boolean guards(BlockPos pos) {
		return index >= 0 && !solved && pos.closerThan(worldPosition, 6);
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putInt("Index", index);
		output.putInt("Target", target);
		output.putBoolean("Solved", solved);
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		index = input.getIntOr("Index", 0);
		target = input.getIntOr("Target", 0);
		solved = input.getBooleanOr("Solved", false);
	}
}
