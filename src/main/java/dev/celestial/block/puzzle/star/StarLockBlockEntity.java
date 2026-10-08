package dev.celestial.block.puzzle.star;

import dev.celestial.puzzle.Attempts;
import dev.celestial.puzzle.PuzzleRewards;
import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModBlocks;
import dev.celestial.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * Звёздный кодовый замок. Комбинация — сид от позиции замка (у каждой постройки своя, «вики-ответа» нет); при первом
 * осмотре замок проявляет фрески в радиусе 20: каждой — созвездие для её цвета. Сверка: все диски (радиус 6) показывают
 * созвездия своих цветов → решено. Ошибка → блокировка (Attempts, 20 с ×2) и из звёздной пыли встают Падшие стражи.
 */
public class StarLockBlockEntity extends BlockEntity {
	private static final int FRESCO_RANGE = 20;
	private static final int DISC_RANGE = 6;
	private boolean setup;

	public StarLockBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.STAR_LOCK, pos, state);
	}

	/** Созвездие, которое нужно выставить для цвета color. */
	private int target(int color) {
		RandomSource random = RandomSource.create(worldPosition.asLong() * 0x9E3779B97F4A7C15L + 0x5741524C4F434BL);
		int[] perm = {0, 1, 2, 3, 4, 5, 6, 7};
		for (int i = 7; i > 0; i--) {  // разные цвета — разные созвездия
			int j = random.nextInt(i + 1);
			int t = perm[i];
			perm[i] = perm[j];
			perm[j] = t;
		}
		return perm[color];
	}

	void ensureSetup(ServerLevel level) {
		if (setup) {
			return;
		}
		setup = true;
		setChanged();
		for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-FRESCO_RANGE, -14, -FRESCO_RANGE), worldPosition.offset(FRESCO_RANGE, 6, FRESCO_RANGE))) {
			BlockState s = level.getBlockState(p);
			if (s.is(ModBlocks.STAR_FRESCO)) {
				level.setBlock(p, s.setValue(StarFrescoBlock.SYMBOL, target(s.getValue(StarFrescoBlock.COLOR))).setValue(StarFrescoBlock.HIDDEN, false),
					Block.UPDATE_CLIENTS);
			}
		}
	}

	void check(ServerLevel level, Player player) {
		ensureSetup(level);
		if (getBlockState().getValue(StarLockBlock.SOLVED)) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.star_lock.solved"));
			return;
		}
		int locked = Attempts.lockedSeconds(level, worldPosition, player);
		if (locked > 0) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.locked_wait", locked));
			return;
		}
		int discs = 0;
		boolean ok = true;
		for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-DISC_RANGE, -2, -DISC_RANGE), worldPosition.offset(DISC_RANGE, 3, DISC_RANGE))) {
			BlockState s = level.getBlockState(p);
			if (s.is(ModBlocks.STAR_DISC)) {
				discs++;
				ok &= s.getValue(StarDiscBlock.SYMBOL) == target(s.getValue(StarDiscBlock.COLOR));
			}
		}
		if (discs > 0 && ok) {
			level.setBlock(worldPosition, getBlockState().setValue(StarLockBlock.SOLVED, true), Block.UPDATE_ALL);
			Attempts.reset(level, worldPosition, player);
			PuzzleRewards.solved(level, worldPosition, player, "star_lock", 6);
			return;
		}
		Attempts.fail(level, worldPosition, player, Component.translatable("puzzle.celestial.star_lock.wrong"));
		for (int i = 0; i < 1 + level.getRandom().nextInt(2); i++) {  // звёздная пыль встаёт стражем
			Mob guard = ModEntities.FALLEN_GUARDIAN.create(level, EntitySpawnReason.MOB_SUMMONED);
			if (guard != null) {
				BlockPos at = worldPosition.offset(level.getRandom().nextInt(5) - 2, 1, level.getRandom().nextInt(5) - 2);
				guard.snapTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, level.getRandom().nextFloat() * 360, 0);
				guard.addTag(dev.celestial.world.abyss.Darkness.NO_REPEL);
				guard.setTarget(player);
				level.addFreshEntity(guard);
				level.sendParticles(ParticleTypes.END_ROD, at.getX() + 0.5, at.getY() + 1, at.getZ() + 0.5, 30, 0.3, 0.8, 0.3, 0.05);
			}
		}
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putBoolean("Setup", setup);
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		setup = input.getBooleanOr("Setup", false);
	}
}
