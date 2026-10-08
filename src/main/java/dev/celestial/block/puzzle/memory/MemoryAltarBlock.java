package dev.celestial.block.puzzle.memory;

import dev.celestial.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
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
import net.minecraft.world.phys.BlockHitResult;
import org.jspecify.annotations.Nullable;

/** Алтарь памяти: ПКМ — показать маршрут по плитам. Хранит загадку ({@link MemoryAltarBlockEntity}). */
public class MemoryAltarBlock extends BaseEntityBlock implements dev.celestial.puzzle.PuzzleInteractive {
	public static final BooleanProperty SOLVED = BooleanProperty.create("solved");

	public MemoryAltarBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(SOLVED, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(SOLVED);
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new MemoryAltarBlockEntity(pos, state);
	}

	@Override
	public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		return level.isClientSide() ? null : createTickerHelper(type, ModBlockEntities.MEMORY_ALTAR, (l, p, s, be) -> be.tick((ServerLevel) l));
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (level instanceof ServerLevel server && level.getBlockEntity(pos) instanceof MemoryAltarBlockEntity altar) {
			altar.show(server, player);
		}
		return InteractionResult.SUCCESS;
	}
}
