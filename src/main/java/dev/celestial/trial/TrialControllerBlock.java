package dev.celestial.trial;

import dev.celestial.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.BlockHitResult;
import org.jspecify.annotations.Nullable;

/** Кристалл испытания: ПКМ — начать испытание этажа. После победы светится и даёт сигнал (открывает печать-двери). */
public class TrialControllerBlock extends Block implements EntityBlock {
	public enum TrialState implements StringRepresentable {
		IDLE, RUNNING, DONE;

		@Override
		public String getSerializedName() {
			return name().toLowerCase();
		}
	}

	public static final EnumProperty<TrialState> STATE = EnumProperty.create("state", TrialState.class);

	public TrialControllerBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(STATE, TrialState.IDLE));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(STATE);
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new TrialControllerBlockEntity(pos, state);
	}

	@Override
	@SuppressWarnings("unchecked")
	public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		return level.isClientSide() || type != ModBlockEntities.TRIAL_CONTROLLER ? null
			: (BlockEntityTicker<T>) (BlockEntityTicker<TrialControllerBlockEntity>) (l, p, s, be) -> be.serverTick((ServerLevel) l);
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (level instanceof ServerLevel server && level.getBlockEntity(pos) instanceof TrialControllerBlockEntity be) {
			be.start(server, player);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	protected boolean isSignalSource(BlockState state) {
		return true;
	}

	@Override
	protected int getSignal(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
		return state.getValue(STATE) == TrialState.DONE ? 15 : 0;
	}
}
