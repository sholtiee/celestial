package dev.celestial.block.jerusalem;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;

/** Камень основания Нового Иерусалима (Откр. 21:19–20): двенадцать самоцветов — одно свойство {@code gem} 0..11, от ясписа до аметиста. */
public class FoundationStoneBlock extends Block {
	public static final IntegerProperty GEM = IntegerProperty.create("gem", 0, 11);

	public FoundationStoneBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(GEM, 0));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(GEM);
	}
}
