package dev.celestial.mech;

import dev.celestial.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
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

/**
 * Приводной пресс: ПКМ слитком (или камнем) — положить стопку, пустой рукой — забрать. Пока на пресс смотрит вращающийся
 * вал или шестерня, каждые {@link DrivePressBlockEntity#STROKE} тиков штамп опускается и выдаёт изделие сверху.
 */
public class DrivePressBlock extends BaseEntityBlock {
	public static final BooleanProperty WORKING = BooleanProperty.create("working");

	public DrivePressBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(WORKING, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(WORKING);
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand, BlockHitResult hit) {
		if (DrivePressBlockEntity.result(stack).isEmpty()) {
			return InteractionResult.TRY_WITH_EMPTY_HAND;
		}
		if (!level.isClientSide() && level.getBlockEntity(pos) instanceof DrivePressBlockEntity be) {
			if (!be.insert(stack)) {
				player.sendOverlayMessage(Component.translatable("block.celestial.drive_press.busy"));
				return InteractionResult.FAIL;
			}
			level.playSound(null, pos, SoundEvents.ITEM_FRAME_ADD_ITEM, SoundSource.BLOCKS, 0.8F, 0.8F);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!level.isClientSide() && level.getBlockEntity(pos) instanceof DrivePressBlockEntity be) {
			ItemStack out = be.take();
			if (out.isEmpty()) {
				player.sendOverlayMessage(Component.translatable(Gears.driven(level, pos)
					? "block.celestial.drive_press.empty" : "block.celestial.drive_press.no_drive"));
			} else if (!player.addItem(out)) {
				player.spawnAtLocation((net.minecraft.server.level.ServerLevel) level, out);
			}
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new DrivePressBlockEntity(pos, state);
	}

	@Override
	public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		return level.isClientSide() ? null : createTickerHelper(type, ModBlockEntities.DRIVE_PRESS, DrivePressBlockEntity::serverTick);
	}
}
