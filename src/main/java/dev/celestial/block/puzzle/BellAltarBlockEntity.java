package dev.celestial.block.puzzle;

import dev.celestial.puzzle.PuzzleRewards;
import dev.celestial.registry.ModBlockEntities;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** Мелодия зависит от позиции алтаря (у каждой святыни своя). Длина растёт: 4 ноты + 1 за каждые 2 колокола рядом. */
public class BellAltarBlockEntity extends BlockEntity {
	private static final int NOTE_GAP = 14;
	private final List<Integer> heard = new ArrayList<>();
	private int playIndex = -1;
	private int playClock;

	public BellAltarBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.BELL_ALTAR, pos, state);
	}

	private List<Integer> melody() {
		RandomSource random = RandomSource.create(worldPosition.asLong() ^ 0x5EEDBE11L);
		List<Integer> notes = new ArrayList<>();
		for (int i = 0; i < 5; i++) {
			notes.add(random.nextInt(5));
		}
		return notes;
	}

	public void playMelody(ServerLevel level, Player player) {
		if (getBlockState().getValue(BellAltarBlock.SOLVED)) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.bells.already"));
			return;
		}
		heard.clear();
		playIndex = 0;
		playClock = 0;
		player.sendOverlayMessage(Component.translatable("puzzle.celestial.bells.listen"));
	}

	void serverTick(ServerLevel level) {
		if (playIndex < 0) {
			return;
		}
		if (playClock++ % NOTE_GAP != 0) {
			return;
		}
		List<Integer> melody = melody();
		if (playIndex >= melody.size()) {
			playIndex = -1;
			return;
		}
		int note = melody.get(playIndex++);
		// звучит и подсвечивается тот колокол рядом, у которого эта нота
		BlockPos bell = findBell(level, note);
		SkyBellBlock.ring(level, bell != null ? bell : worldPosition.above(), note);
	}

	private BlockPos findBell(ServerLevel level, int note) {
		for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-12, -6, -12), worldPosition.offset(12, 6, 12))) {
			BlockState s = level.getBlockState(p);
			if (s.getBlock() instanceof SkyBellBlock && s.getValue(SkyBellBlock.NOTE) == note) {
				return p.immutable();
			}
		}
		return null;
	}

	void onBellRung(ServerLevel level, int note, Player player) {
		if (getBlockState().getValue(BellAltarBlock.SOLVED) || playIndex >= 0) {
			return;
		}
		List<Integer> melody = melody();
		heard.add(note);
		int i = heard.size() - 1;
		if (!melody.get(i).equals(note)) {
			heard.clear();
			level.playSound(null, worldPosition, SoundEvents.NOTE_BLOCK_BASS.value(), SoundSource.BLOCKS, 1.0F, 0.5F);
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.bells.wrong"));
			return;
		}
		if (heard.size() == melody.size()) {
			level.setBlock(worldPosition, getBlockState().setValue(BellAltarBlock.SOLVED, true), Block.UPDATE_ALL);
			PuzzleRewards.solved(level, worldPosition, player, "bells");
		}
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
	}
}
