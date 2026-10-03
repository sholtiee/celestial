package dev.celestial.starlight;

import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
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
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jspecify.annotations.Nullable;

/**
 * Звездоловка: ночью под открытым небом копит звёздный свет (CHARGE 0–4 — для вида и подсветки).
 * Склянкой по ней — Флакон звёздного света (стоит одно деление).
 */
public class StarCollectorBlock extends BaseEntityBlock {
	public static final IntegerProperty CHARGE = IntegerProperty.create("charge", 0, 4);
	private static final VoxelShape SHAPE = Block.box(2, 0, 2, 14, 13, 14);

	public StarCollectorBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(CHARGE, 0));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(CHARGE);
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
		return new StarCollectorBlockEntity(pos, state);
	}

	@Override
	@SuppressWarnings("unchecked")
	public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		return level.isClientSide() || type != ModBlockEntities.STAR_COLLECTOR ? null
			: (BlockEntityTicker<T>) (BlockEntityTicker<StarCollectorBlockEntity>) (l, p, s, be) -> be.serverTick((ServerLevel) l, s);
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand,
		BlockHitResult hit) {
		if (!stack.is(Items.GLASS_BOTTLE)) {
			return InteractionResult.TRY_WITH_EMPTY_HAND;
		}
		if (!(level.getBlockEntity(pos) instanceof StarCollectorBlockEntity be)) {
			return InteractionResult.PASS;
		}
		if (!level.isClientSide()) {
			if (!be.takeFlask()) {
				player.sendOverlayMessage(Component.translatable("block.celestial.star_collector.empty"));
				return InteractionResult.SUCCESS;
			}
			stack.consume(1, player);
			ItemStack flask = new ItemStack(ModItems.STARLIGHT_FLASK);
			if (!player.getInventory().add(flask)) {
				player.spawnAtLocation((net.minecraft.server.level.ServerLevel) level, flask);
			}
			level.playSound(null, pos, SoundEvents.BOTTLE_FILL, SoundSource.BLOCKS, 1.0F, 1.4F);
			level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.0F, 1.6F);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!level.isClientSide() && level.getBlockEntity(pos) instanceof StarCollectorBlockEntity be) {
			player.sendOverlayMessage(Component.translatable("block.celestial.star_collector.charge", be.charge(), StarCollectorBlockEntity.MAX));
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		int charge = state.getValue(CHARGE);
		if (charge > 0 && random.nextInt(5 - charge) == 0) {
			level.addParticle(dev.celestial.registry.ModParticles.STARLIGHT, pos.getX() + 0.5 + (random.nextDouble() - 0.5) * 0.6, pos.getY() + 0.95,
				pos.getZ() + 0.5 + (random.nextDouble() - 0.5) * 0.6, 0, 0.02, 0);
		}
	}
}
