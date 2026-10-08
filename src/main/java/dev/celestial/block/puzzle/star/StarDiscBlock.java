package dev.celestial.block.puzzle.star;

import net.minecraft.core.BlockPos;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Звёздный диск кодового замка: оправа одного из четырёх цветов, на лице — созвездие (8 символов). ПКМ — следующее созвездие.
 * Неразрушим. Нужное созвездие для своего цвета подсказывает фреска того же цвета где-то в постройке.
 */
public class StarDiscBlock extends Block implements dev.celestial.puzzle.PuzzleInteractive {
	public static final IntegerProperty COLOR = IntegerProperty.create("color", 0, 3);
	public static final IntegerProperty SYMBOL = IntegerProperty.create("symbol", 0, 7);

	public StarDiscBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(COLOR, 0).setValue(SYMBOL, 0));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(COLOR, SYMBOL);
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!level.isClientSide()) {
			level.setBlock(pos, state.cycle(SYMBOL), Block.UPDATE_ALL);
			level.playSound(null, pos, net.minecraft.sounds.SoundEvents.AMETHYST_BLOCK_RESONATE, net.minecraft.sounds.SoundSource.BLOCKS,
				0.8F, 0.8F + state.getValue(SYMBOL) * 0.1F);
		}
		return InteractionResult.SUCCESS;
	}
}
