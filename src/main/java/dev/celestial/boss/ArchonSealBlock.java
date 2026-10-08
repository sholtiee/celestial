package dev.celestial.boss;

import dev.celestial.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import org.jspecify.annotations.Nullable;

/** Печать Архонта в центре арены: будит босса, когда игрок (не в творческом) подходит ближе 9 блоков. */
public class ArchonSealBlock extends BaseEntityBlock {
	public static final BooleanProperty AWAKENED = BooleanProperty.create("awakened");

	public ArchonSealBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(AWAKENED, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(AWAKENED);
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new ArchonSealBlockEntity(pos, state);
	}

	@Override
	public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		return level.isClientSide() || state.getValue(AWAKENED) ? null
			: createTickerHelper(type, ModBlockEntities.ARCHON_SEAL, ArchonSealBlockEntity::serverTick);
	}
}
