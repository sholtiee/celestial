package dev.celestial.block.puzzle.ice;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;

/** Плита-гнездо в полу зала: загорается, когда на ней стоит рунная глыба. Состояние ставит {@link GlacierHallBlockEntity}. */
public class GlacierNestBlock extends Block {
	public static final BooleanProperty OCCUPIED = BooleanProperty.create("occupied");

	public GlacierNestBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(OCCUPIED, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(OCCUPIED);
	}
}
