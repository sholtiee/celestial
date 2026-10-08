package dev.celestial.block.puzzle.star;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;

/**
 * Фреска-подсказка кодового замка: цветная рамка и созвездие. Пока замок её не «разбудил» (HIDDEN), на ней только звёздная пыль;
 * замок при первом осмотре ставит каждой фреске созвездие для её цвета — у каждой обсерватории своя комбинация.
 */
public class StarFrescoBlock extends Block {
	public static final IntegerProperty COLOR = StarDiscBlock.COLOR;
	public static final IntegerProperty SYMBOL = StarDiscBlock.SYMBOL;
	public static final BooleanProperty HIDDEN = BooleanProperty.create("hidden");

	public StarFrescoBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(COLOR, 0).setValue(SYMBOL, 0).setValue(HIDDEN, true));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(COLOR, SYMBOL, HIDDEN);
	}
}
