package dev.celestial.astral;

import dev.celestial.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
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

/**
 * Гнездо Звёздного диска (поле 5×5 вокруг диска): ПКМ Звёздным камнем — вставить, пустой рукой — вынуть (пока хор не собран).
 * Неразрушимо; клик с блоком в руке гнездо поглощает (охрана зоны загадки).
 */
public class StarSocketBlock extends Block implements dev.celestial.puzzle.PuzzleInteractive {
	public static final BooleanProperty FILLED = BooleanProperty.create("filled");
	private static final VoxelShape SHAPE = Block.box(0, 0, 0, 16, 4, 16);

	public StarSocketBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(FILLED, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FILLED);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand, BlockHitResult hit) {
		if (!stack.is(ModItems.STAR_STONE)) {
			return InteractionResult.TRY_WITH_EMPTY_HAND;
		}
		if (state.getValue(FILLED)) {
			return InteractionResult.PASS;
		}
		if (level instanceof ServerLevel server) {
			StarDiskBlockEntity disk = StarDiskBlockEntity.find(server, pos);
			if (disk == null || disk.solved() || !disk.mayTouch(server, player)) {
				return InteractionResult.FAIL;
			}
			level.setBlock(pos, state.setValue(FILLED, true), Block.UPDATE_ALL);
			stack.consume(1, player);
			level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_PLACE, SoundSource.BLOCKS, 1.0F, 1.4F);
			disk.check(server, player);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!state.getValue(FILLED)) {
			return InteractionResult.PASS;
		}
		if (level instanceof ServerLevel server) {
			StarDiskBlockEntity disk = StarDiskBlockEntity.find(server, pos);
			if (disk != null && disk.solved()) {
				return InteractionResult.FAIL;  // собранный хор держит свои звёзды
			}
			level.setBlock(pos, state.setValue(FILLED, false), Block.UPDATE_ALL);
			if (!player.addItem(new ItemStack(ModItems.STAR_STONE))) {
				player.spawnAtLocation(server, new ItemStack(ModItems.STAR_STONE));
			}
			level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.BLOCKS, 0.8F, 1.2F);
		}
		return InteractionResult.SUCCESS;
	}
}
