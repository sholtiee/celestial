package dev.celestial.starlight;

import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
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
 * Оберег: пьедестал с заряженным кристаллом. Пока горит (топливо — Флаконы звёздного света),
 * в радиусе 16 блоков не появляются Тени и твари Бездны, а страх тьмы не растёт.
 */
public class WardBlock extends BaseEntityBlock {
	public static final BooleanProperty CRYSTAL = BooleanProperty.create("crystal");
	public static final BooleanProperty LIT = BooleanProperty.create("lit");
	private static final VoxelShape SHAPE = Block.box(3, 0, 3, 13, 16, 13);

	public WardBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(CRYSTAL, false).setValue(LIT, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(CRYSTAL, LIT);
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
		return new WardBlockEntity(pos, state);
	}

	@Override
	@SuppressWarnings("unchecked")
	public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		return level.isClientSide() || type != ModBlockEntities.WARD ? null
			: (BlockEntityTicker<T>) (BlockEntityTicker<WardBlockEntity>) (l, p, s, be) -> be.serverTick((ServerLevel) l, s);
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand,
		BlockHitResult hit) {
		if (!(level.getBlockEntity(pos) instanceof WardBlockEntity be)) {
			return InteractionResult.PASS;
		}
		if (stack.is(ModItems.CHARGED_CRYSTAL) && !state.getValue(CRYSTAL)) {
			if (!level.isClientSide()) {
				stack.consume(1, player);
				level.setBlock(pos, state.setValue(CRYSTAL, true), Block.UPDATE_ALL);
				level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_PLACE, SoundSource.BLOCKS, 1.0F, 1.0F);
			}
			return InteractionResult.SUCCESS;
		}
		if (stack.is(ModItems.STARLIGHT_FLASK)) {
			if (!level.isClientSide()) {
				if (be.addFlask()) {
					stack.consume(1, player);
					ItemStack bottle = new ItemStack(Items.GLASS_BOTTLE);
					if (!player.getInventory().add(bottle)) {
						player.spawnAtLocation((net.minecraft.server.level.ServerLevel) level, bottle);
					}
					level.playSound(null, pos, SoundEvents.BEACON_POWER_SELECT, SoundSource.BLOCKS, 1.0F, 1.6F);
				} else {
					player.sendOverlayMessage(Component.translatable("block.celestial.ward.full"));
				}
			}
			return InteractionResult.SUCCESS;
		}
		return InteractionResult.TRY_WITH_EMPTY_HAND;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!level.isClientSide() && level.getBlockEntity(pos) instanceof WardBlockEntity be) {
			player.sendOverlayMessage(!state.getValue(CRYSTAL) ? Component.translatable("block.celestial.ward.no_crystal")
				: Component.translatable("block.celestial.ward.fuel", be.fuel() / 1200));
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	protected void affectNeighborsAfterRemoval(BlockState state, ServerLevel level, BlockPos pos, boolean movedByPiston) {
		if (state.getValue(CRYSTAL)) {
			Block.popResource(level, pos, new ItemStack(ModItems.CHARGED_CRYSTAL));
		}
		super.affectNeighborsAfterRemoval(state, level, pos, movedByPiston);
	}
}
