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

/** Звёздный алтарь (вершина): будит Безликого, когда подходит игрок (не в творческом), собравший не меньше 7 хоров из 9. */
public class StarAltarBlock extends BaseEntityBlock {
	public static final BooleanProperty AWAKENED = BooleanProperty.create("awakened");

	public StarAltarBlock(Properties properties) {
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

	/** После светлой концовки алтарь ведёт в Новый Иерусалим. */
	@Override
	protected net.minecraft.world.InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, net.minecraft.world.entity.player.Player player,
			net.minecraft.world.phys.BlockHitResult hit) {
		if (player instanceof net.minecraft.server.level.ServerPlayer sp && dev.celestial.story.NewJerusalem.open(sp.level().getServer())
				&& level.getEntitiesOfClass(Faceless.class, player.getBoundingBox().inflate(48), f -> !f.defeated()).isEmpty()) {
			dev.celestial.story.NewJerusalem.bring(sp);
			return net.minecraft.world.InteractionResult.SUCCESS;
		}
		return net.minecraft.world.InteractionResult.PASS;
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new StarAltarBlockEntity(pos, state);
	}

	@Override
	public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		return level.isClientSide() || state.getValue(AWAKENED) ? null
			: createTickerHelper(type, ModBlockEntities.STAR_ALTAR, StarAltarBlockEntity::serverTick);
	}
}
