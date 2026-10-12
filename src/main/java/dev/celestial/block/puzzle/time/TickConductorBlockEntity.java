package dev.celestial.block.puzzle.time;

import dev.celestial.chrono.PendulumBlock;
import dev.celestial.puzzle.PuzzleRewards;
import dev.celestial.puzzle.PuzzleZone;
import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModBlocks;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;

/**
 * «Ход маятника». Платформы зала твёрдые половину такта; платформа с фазой k опережает нулевую на k четвертей —
 * по ряду бежит волна (шаблон ставит фазы убывающими по пути: следующая появляется на четверть такта позже текущей,
 * на прыжок — четверть такта). Такт — 32 «доли»; за тик проходит 1 доля (окно 8 тиков — трудно), если в радиусе 10 качается
 * лёгкий маятник — 2 (4 тика — не успеть), если только тяжёлый — 0,5 (16 тиков — успеваешь). Древний лёгкий маятник останавливает Камертон, тяжёлый пускается рукой.
 * Финиш засчитывается, только если игрок за последние 3 с стоял на платформе (не перелетел жемчугом/элитрами) и не летит.
 */
public class TickConductorBlockEntity extends BlockEntity implements PuzzleZone {
	public static final int PERIOD = 32;
	private static final int RANGE = 20;
	private final List<BlockPos> platforms = new ArrayList<>();
	private final Map<UUID, Long> lastStep = new HashMap<>();
	private boolean scanned;
	private boolean solved;
	private double beat;
	private double speed = 1.0;
	private AABB zone = new AABB(BlockPos.ZERO);

	public TickConductorBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.TICK_CONDUCTOR, pos, state);
	}

	private void scan(ServerLevel level) {
		platforms.clear();
		for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-RANGE, -12, -RANGE), worldPosition.offset(RANGE, 4, RANGE))) {
			if (level.getBlockState(p).is(ModBlocks.TICK_PLATFORM)) {
				platforms.add(p.immutable());
			}
		}
		AABB box = new AABB(worldPosition);
		for (BlockPos p : platforms) {
			box = box.minmax(new AABB(p));
		}
		zone = box.inflate(2, 0, 2).expandTowards(0, 5, 0).expandTowards(0, -8, 0);
		scanned = true;
	}

	/** Сколько долей такта проходит за тик — по маятникам рядом. */
	private double tempo(ServerLevel level) {
		boolean swift = false, heavy = false;
		for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-10, -10, -10), worldPosition.offset(10, 4, 10))) {
			BlockState s = level.getBlockState(p);
			if (s.getBlock() instanceof PendulumBlock pendulum && s.getValue(PendulumBlock.SWINGING)) {
				if (pendulum.scale > 1.0F) {
					swift = true;
				} else if (pendulum.scale < 1.0F) {
					heavy = true;
				}
			}
		}
		return swift ? 2.0 : heavy ? 0.5 : 1.0;
	}

	public double speed() {
		return speed;
	}

	void tick(ServerLevel level) {
		if (!scanned) {
			scan(level);
		}
		if (solved) {
			return;
		}
		if (level.getGameTime() % 10 == 0) {
			speed = tempo(level);
		}
		double before = beat;
		beat = (beat + speed) % PERIOD;
		if (Math.floor(before / (PERIOD / 4.0)) != Math.floor(beat / (PERIOD / 4.0))) {
			level.playSound(null, worldPosition, SoundEvents.NOTE_BLOCK_HAT.value(), SoundSource.BLOCKS, 0.6F, speed > 1 ? 1.6F : speed < 1 ? 0.7F : 1.1F);
		}
		for (BlockPos p : platforms) {
			BlockState s = level.getBlockState(p);
			if (!s.is(ModBlocks.TICK_PLATFORM)) {
				continue;
			}
			double local = (beat + s.getValue(TickPlatformBlock.PHASE) * PERIOD / 4.0) % PERIOD;
			boolean solid = local < PERIOD / 2.0;
			if (s.getValue(TickPlatformBlock.SOLID) != solid) {
				level.setBlock(p, s.setValue(TickPlatformBlock.SOLID, solid), Block.UPDATE_CLIENTS);
			}
		}
		for (ServerPlayer player : level.getEntitiesOfClass(ServerPlayer.class, zone)) {
			if (level.getBlockState(player.getBlockPosBelowThatAffectsMyMovement()).is(ModBlocks.TICK_PLATFORM)
				|| level.getBlockState(player.blockPosition()).is(ModBlocks.TICK_PLATFORM)) {
				lastStep.put(player.getUUID(), level.getGameTime());
			}
		}
	}

	/** Игрок наступил на финиш. */
	void reach(ServerLevel level, Player player) {
		if (solved || player.isCreative() || player.isSpectator()) {
			return;
		}
		Long step = lastStep.get(player.getUUID());
		if (player.isFallFlying() || step == null || level.getGameTime() - step > 60) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.tick_platforms.walk"));
			return;
		}
		solved = true;
		for (BlockPos p : platforms) {
			BlockState s = level.getBlockState(p);
			if (s.is(ModBlocks.TICK_PLATFORM)) {
				level.setBlock(p, s.setValue(TickPlatformBlock.SOLID, true), Block.UPDATE_ALL);  // обратный путь — по твёрдым
			}
		}
		setChanged();
		PuzzleRewards.solved(level, player.blockPosition(), player, "tick_platforms", 10);
	}

	@Override
	public boolean guards(BlockPos pos) {
		return scanned && !solved && zone.contains(pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5);
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
	}

	static TickConductorBlockEntity find(ServerLevel level, BlockPos near) {
		for (BlockPos p : BlockPos.betweenClosed(near.offset(-RANGE, -4, -RANGE), near.offset(RANGE, 12, RANGE))) {
			if (level.getBlockEntity(p) instanceof TickConductorBlockEntity c) {
				return c;
			}
		}
		return null;
	}
}
