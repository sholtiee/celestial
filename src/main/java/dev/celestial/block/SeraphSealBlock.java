package dev.celestial.block;

import dev.celestial.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import org.jspecify.annotations.Nullable;

/** Печать Серафима в центре арены: когда рядом появляется игрок, пробуждает Падшего Серафима (один раз). */
public class SeraphSealBlock extends Block implements EntityBlock {
	public static final BooleanProperty AWAKENED = BooleanProperty.create("awakened");

	public SeraphSealBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(AWAKENED, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(AWAKENED);
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new SeraphSealBlockEntity(pos, state);
	}

	@Override
	@SuppressWarnings("unchecked")
	public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		return level.isClientSide() || state.getValue(AWAKENED) || type != ModBlockEntities.SERAPH_SEAL ? null
			: (BlockEntityTicker<T>) (BlockEntityTicker<SeraphSealBlockEntity>) SeraphSealBlockEntity::serverTick;
	}
}
