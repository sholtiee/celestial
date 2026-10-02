package dev.celestial.block;

import dev.celestial.registry.ModItems;
import dev.celestial.story.StoryEvents;
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
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Небесный алтарь: в него вставляются Осколок Пламени, Сердце Пустоты и Осколок Света. */
public class CelestialAltarBlock extends Block {
	public static final BooleanProperty FLAME = BooleanProperty.create("flame");
	public static final BooleanProperty VOID = BooleanProperty.create("void");
	public static final BooleanProperty LIGHT = BooleanProperty.create("light");
	private static final VoxelShape SHAPE = Block.box(1, 0, 1, 15, 14, 15);

	public CelestialAltarBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(FLAME, false).setValue(VOID, false).setValue(LIGHT, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FLAME, VOID, LIGHT);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	public static boolean isComplete(BlockState state) {
		return state.getValue(FLAME) && state.getValue(VOID) && state.getValue(LIGHT);
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand, BlockHitResult hit) {
		if (isComplete(state)) {
			return InteractionResult.PASS;
		}
		BooleanProperty slot = stack.is(ModItems.FLAME_SHARD) ? FLAME : stack.is(ModItems.VOID_HEART) ? VOID : stack.is(ModItems.LIGHT_SHARD) ? LIGHT : null;
		if (slot == null) {
			if (!level.isClientSide()) {
				player.sendOverlayMessage(Component.translatable("block.celestial.celestial_altar.hint"));
			}
			return InteractionResult.PASS;
		}
		if (state.getValue(slot)) {
			return InteractionResult.FAIL;
		}
		if (level instanceof ServerLevel serverLevel) {
			BlockState updated = state.setValue(slot, true);
			serverLevel.setBlock(pos, updated, Block.UPDATE_ALL);
			stack.consume(1, player);
			serverLevel.playSound(null, pos, SoundEvents.END_PORTAL_FRAME_FILL, SoundSource.BLOCKS, 1.0F, 1.2F);
			serverLevel.sendParticles(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 1.1, pos.getZ() + 0.5, 25, 0.2, 0.3, 0.2, 0.05);
			if (isComplete(updated)) {
				StoryEvents.onAltarComplete(serverLevel, pos);
			}
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		int filled = (state.getValue(FLAME) ? 1 : 0) + (state.getValue(VOID) ? 1 : 0) + (state.getValue(LIGHT) ? 1 : 0);
		for (int i = 0; i < filled; i++) {
			level.addParticle(isComplete(state) ? ParticleTypes.END_ROD : ParticleTypes.WAX_ON,
				pos.getX() + 0.5 + (random.nextDouble() - 0.5) * 0.6, pos.getY() + 1.0, pos.getZ() + 0.5 + (random.nextDouble() - 0.5) * 0.6, 0, 0.05, 0);
		}
	}
}
