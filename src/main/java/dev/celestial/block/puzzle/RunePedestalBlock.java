package dev.celestial.block.puzzle;

import dev.celestial.puzzle.PuzzleRewards;
import dev.celestial.puzzle.Riddles;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;

/** Рунный пьедестал: ПКМ рукой — прочесть загадку, ПКМ предметом-ответом — разгадать (ответ забирается). */
public class RunePedestalBlock extends Block {
	public static final IntegerProperty RIDDLE = IntegerProperty.create("riddle", 0, Riddles.COUNT - 1);
	public static final BooleanProperty SOLVED = BooleanProperty.create("solved");

	public RunePedestalBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(RIDDLE, 0).setValue(SOLVED, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(RIDDLE, SOLVED);
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!level.isClientSide()) {
			player.sendSystemMessage(state.getValue(SOLVED) ? Component.translatable("puzzle.celestial.riddle.solved")
				: Component.translatable("puzzle.celestial.riddle." + state.getValue(RIDDLE)));
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand, BlockHitResult hit) {
		if (state.getValue(SOLVED)) {
			return InteractionResult.PASS;
		}
		if (!stack.is(Riddles.answer(state.getValue(RIDDLE)))) {
			if (level instanceof ServerLevel server) {
				server.playSound(null, pos, SoundEvents.NOTE_BLOCK_BASS.value(), SoundSource.BLOCKS, 1.0F, 0.5F);
				player.sendOverlayMessage(Component.translatable("puzzle.celestial.riddle.wrong"));
			}
			return InteractionResult.FAIL;
		}
		if (level instanceof ServerLevel server) {
			stack.consume(1, player);
			server.setBlock(pos, state.setValue(SOLVED, true), Block.UPDATE_ALL);
			PuzzleRewards.solved(server, pos, player, "riddle");
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	protected boolean isSignalSource(BlockState state) {
		return true;
	}

	@Override
	protected int getSignal(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
		return state.getValue(SOLVED) ? 15 : 0;
	}
}
