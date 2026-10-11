package dev.celestial.chrono;

import dev.celestial.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.BlockHitResult;
import org.jspecify.annotations.Nullable;

/**
 * Маятник: часовой корпус, под которым (или над которым, если внизу опора — тогда как метроном) качается маятник.
 * Пока качается — вокруг сфера R={@link #RADIUS}, где время идёт иначе: Быстрый маятник ускоряет, Тяжёлый — замедляет.
 * ПКМ пустой рукой — остановить/пустить. Древние маятники ({@code sealed}) рукой не останавливаются — только Камертоном (загадки, арена Часовщика).
 */
public class PendulumBlock extends BaseEntityBlock {
	public static final EnumProperty<Direction> FACING = BlockStateProperties.HORIZONTAL_FACING;
	public static final BooleanProperty SWINGING = BooleanProperty.create("swinging");
	public static final BooleanProperty SEALED = BooleanProperty.create("sealed");
	public static final double RADIUS = 6.0;

	/** Масштаб хода в зоне. */
	public final float scale;
	/** Период качания в тиках (для отрисовки). */
	public final int period;

	public PendulumBlock(float scale, int period, Properties properties) {
		super(properties);
		this.scale = scale;
		this.period = period;
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(SWINGING, true).setValue(SEALED, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING, SWINGING, SEALED);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}

	/** Камертон останавливает любой маятник, и древний тоже (арена Часовщика, загадки): звон в лад гасит качание. */
	@Override
	protected InteractionResult useItemOn(net.minecraft.world.item.ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
		net.minecraft.world.InteractionHand hand, BlockHitResult hit) {
		if (!stack.is(dev.celestial.registry.ModItems.TUNING_FORK)) {
			return InteractionResult.TRY_WITH_EMPTY_HAND;
		}
		if (!state.getValue(SWINGING)) {
			return InteractionResult.PASS;
		}
		level.setBlock(pos, state.setValue(SWINGING, false), Block.UPDATE_ALL);
		level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 1.5F, 0.7F);
		level.playSound(null, pos, SoundEvents.CHAIN_BREAK, SoundSource.BLOCKS, 1.0F, 0.5F);
		if (level instanceof net.minecraft.server.level.ServerLevel server) {
			server.sendParticles(net.minecraft.core.particles.ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 20, 0.4, 0.6, 0.4, 0.05);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (state.getValue(SEALED)) {
			if (!level.isClientSide()) {
				player.sendOverlayMessage(net.minecraft.network.chat.Component.translatable("block.celestial.pendulum.sealed"));
			}
			return InteractionResult.SUCCESS;
		}
		boolean swinging = !state.getValue(SWINGING);
		level.setBlock(pos, state.setValue(SWINGING, swinging), Block.UPDATE_ALL);
		level.playSound(null, pos, swinging ? SoundEvents.CHAIN_PLACE : SoundEvents.CHAIN_BREAK, SoundSource.BLOCKS, 0.8F, swinging ? 1.4F : 0.7F);
		return InteractionResult.SUCCESS;
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new PendulumBlockEntity(pos, state);
	}

	@Override
	public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		if (!state.getValue(SWINGING)) {
			return null;
		}
		return createTickerHelper(type, ModBlockEntities.PENDULUM, level.isClientSide() ? PendulumBlockEntity::clientTick : PendulumBlockEntity::serverTick);
	}
}
