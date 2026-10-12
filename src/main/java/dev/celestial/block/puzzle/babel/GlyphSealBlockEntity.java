package dev.celestial.block.puzzle.babel;

import dev.celestial.puzzle.Attempts;
import dev.celestial.puzzle.PuzzleRewards;
import dev.celestial.puzzle.PuzzleZone;
import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModBlocks;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * Ответ замка ({@code Answer} — номера слов) и сверка: колёса в радиусе 6 читаются слева направо (по x, затем по z),
 * как их ставит шаблон. Верно — {@link PuzzleRewards#solved}, неверно — {@link Attempts#fail} (блокировка растёт).
 */
public class GlyphSealBlockEntity extends BlockEntity implements PuzzleZone {
	private int[] answer = {0, 1, 2, 3};

	public GlyphSealBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.GLYPH_SEAL, pos, state);
	}

	public boolean solved() {
		return getBlockState().getValue(GlyphSealBlock.SOLVED);
	}

	private List<BlockPos> wheels(Level level) {
		List<BlockPos> out = new ArrayList<>();
		for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-6, -3, -6), worldPosition.offset(6, 3, 6))) {
			if (level.getBlockState(p).is(ModBlocks.GLYPH_WHEEL)) {
				out.add(p.immutable());
			}
		}
		out.sort(Comparator.comparingInt((BlockPos p) -> p.getX()).thenComparingInt(p -> p.getZ()));
		return out;
	}

	void check(ServerLevel level, Player player) {
		if (player.isSpectator()) {
			return;
		}
		if (solved()) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.babel.solved"));
			return;
		}
		if (player.isCreative()) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.babel.creative"));
			return;
		}
		int locked = Attempts.lockedSeconds(level, worldPosition, player);
		if (locked > 0) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.locked_wait", locked));
			return;
		}
		List<BlockPos> wheels = wheels(level);
		boolean right = wheels.size() == answer.length;
		for (int i = 0; right && i < answer.length; i++) {
			right = level.getBlockState(wheels.get(i)).getValue(GlyphWheelBlock.GLYPH) == answer[i];
		}
		if (right) {
			level.setBlock(worldPosition, getBlockState().setValue(GlyphSealBlock.SOLVED, true), Block.UPDATE_ALL);
			level.playSound(null, worldPosition, SoundEvents.BELL_BLOCK, SoundSource.BLOCKS, 2.0F, 1.2F);
			Attempts.reset(level, worldPosition, player);
			PuzzleRewards.solved(level, worldPosition, player, "babel", 12);
		} else {
			level.playSound(null, worldPosition, SoundEvents.DECORATED_POT_SHATTER, SoundSource.BLOCKS, 1.0F, 0.6F);
			Attempts.fail(level, worldPosition, player, Component.translatable("puzzle.celestial.babel.wrong"));
		}
	}

	@Override
	public boolean guards(BlockPos pos) {
		return !solved() && pos.closerThan(worldPosition, 9);
	}

	/** Печать рядом с колесом (для колеса: решено ли уже). */
	static BlockPos findSeal(Level level, BlockPos near) {
		for (BlockPos p : BlockPos.betweenClosed(near.offset(-6, -3, -6), near.offset(6, 3, 6))) {
			if (level.getBlockState(p).is(ModBlocks.GLYPH_SEAL)) {
				return p.immutable();
			}
		}
		return near;
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putIntArray("Answer", answer);
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		input.getIntArray("Answer").filter(a -> a.length > 0).ifPresent(a -> answer = a);
	}
}
