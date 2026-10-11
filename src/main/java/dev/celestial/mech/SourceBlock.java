package dev.celestial.mech;

import dev.celestial.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CampfireBlock;
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
 * Источник оборотов. Выход — грань {@link #FACING} (ставишь «лицом» к детали, по которой кликнул).
 * Часовая пружина: ПКМ пустой рукой — завести на 30 с (до 2 мин). Паровой котёл: работает, пока под ним огонь, лава или магма.
 */
public class SourceBlock extends BaseEntityBlock {
	public static final EnumProperty<Direction> FACING = BlockStateProperties.FACING;
	public static final BooleanProperty ACTIVE = BooleanProperty.create("active");
	public static final int WIND = 600;
	public static final int MAX_WIND = 2400;

	public enum Kind { SPRING, ENGINE }

	private final Kind kind;

	public SourceBlock(Kind kind, Properties properties) {
		super(properties);
		this.kind = kind;
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(ACTIVE, false));
	}

	public Kind kind() {
		return kind;
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING, ACTIVE);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		Direction out = context.getClickedFace().getOpposite();
		if (kind == Kind.ENGINE && out == Direction.DOWN) {
			out = context.getHorizontalDirection();  // котёл снизу греется — выход вниз ему не нужен
		}
		return defaultBlockState().setValue(FACING, out);
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (kind != Kind.SPRING) {
			return InteractionResult.PASS;
		}
		if (!level.isClientSide() && level.getBlockEntity(pos) instanceof SourceBlockEntity be) {
			be.wind();
			level.playSound(null, pos, SoundEvents.CROSSBOW_LOADING_MIDDLE.value(), SoundSource.BLOCKS, 0.9F, 0.8F + level.getRandom().nextFloat() * 0.2F);
			player.sendOverlayMessage(Component.translatable("block.celestial.clock_spring.wound", be.wound() / 20));
		}
		return InteractionResult.SUCCESS;
	}

	/** Греет ли котёл то, что под ним. */
	public static boolean heated(Level level, BlockPos pos) {
		BlockState below = level.getBlockState(pos.below());
		return below.is(Blocks.LAVA) || below.is(BlockTags.FIRE) || below.is(Blocks.MAGMA_BLOCK)
			|| (below.getBlock() instanceof CampfireBlock && below.getValue(CampfireBlock.LIT));
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new SourceBlockEntity(pos, state);
	}

	@Override
	public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		return createTickerHelper(type, ModBlockEntities.MECH_SOURCE, level.isClientSide() ? SourceBlockEntity::clientTick : SourceBlockEntity::serverTick);
	}
}
