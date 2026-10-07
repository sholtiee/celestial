package dev.celestial.block.puzzle;

import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.BlockGetter;
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
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jspecify.annotations.Nullable;

/**
 * Замок трёх лучей: постамент с тремя гнёздами-самоцветами. Самоцвет горит, пока его цвет доходит до родного приёмника.
 * ПКМ — подсказка о том, что горит, и Камертон тому, у кого его нет (без него зеркала не повернуть).
 */
public class BeamLockBlock extends BaseEntityBlock implements dev.celestial.puzzle.PuzzleInteractive {
	public static final BooleanProperty RED = BooleanProperty.create("red");
	public static final BooleanProperty GREEN = BooleanProperty.create("green");
	public static final BooleanProperty BLUE = BooleanProperty.create("blue");
	public static final BooleanProperty SOLVED = BooleanProperty.create("solved");
	private static final VoxelShape SHAPE = Block.box(1, 0, 1, 15, 14, 15);

	public BeamLockBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(RED, false).setValue(GREEN, false).setValue(BLUE, false).setValue(SOLVED, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(RED, GREEN, BLUE, SOLVED);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new BeamLockBlockEntity(pos, state);
	}

	@Override
	public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		return level.isClientSide() ? null : createTickerHelper(type, ModBlockEntities.BEAM_LOCK, BeamLockBlockEntity::serverTick);
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!level.isClientSide()) {
			if (state.getValue(SOLVED)) {
				player.sendOverlayMessage(Component.translatable("puzzle.celestial.beam_lock.solved"));
				return InteractionResult.SUCCESS;
			}
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.beam_lock.status",
				mark(state.getValue(RED), "red", ChatFormatting.RED), mark(state.getValue(GREEN), "green", ChatFormatting.GREEN),
				mark(state.getValue(BLUE), "blue", ChatFormatting.BLUE)));
			if (!player.getInventory().contains(s -> s.is(ModItems.TUNING_FORK))) {
				player.getInventory().add(new ItemStack(ModItems.TUNING_FORK));
				player.sendSystemMessage(Component.translatable("puzzle.celestial.beam_lock.fork").withStyle(ChatFormatting.AQUA));
			}
		}
		return InteractionResult.SUCCESS;
	}

	private static Component mark(boolean lit, String color, ChatFormatting format) {
		return Component.translatable("puzzle.celestial.beam_lock." + color).withStyle(lit ? format : ChatFormatting.DARK_GRAY)
			.append(Component.literal(lit ? " ✦" : " ✧"));
	}
}
