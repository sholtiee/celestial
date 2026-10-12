package dev.celestial.block.puzzle.babel;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;

/** Колесо замка «Смешение языков»: показывает глиф вавилонского письма; ПКМ — следующий, крадучись — предыдущий. Неразрушимо. */
public class GlyphWheelBlock extends Block implements dev.celestial.puzzle.PuzzleInteractive {
	public static final EnumProperty<Direction> FACING = HorizontalDirectionalBlock.FACING;
	public static final IntegerProperty GLYPH = BabelGlyphBlock.GLYPH;

	public GlyphWheelBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(GLYPH, 0));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING, GLYPH);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
	}

	/** С Глиняной табличкой в руке клик — чтение знака (предмет), а не поворот/подсказка. */
	@Override
	protected InteractionResult useItemOn(net.minecraft.world.item.ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
		net.minecraft.world.InteractionHand hand, BlockHitResult hit) {
		return stack.is(dev.celestial.registry.ModItems.CLAY_TABLET) ? InteractionResult.PASS : InteractionResult.TRY_WITH_EMPTY_HAND;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!level.isClientSide() && !player.isSpectator()) {
			if (level.getBlockEntity(GlyphSealBlockEntity.findSeal(level, pos)) instanceof GlyphSealBlockEntity seal && seal.solved()) {
				return InteractionResult.SUCCESS;
			}
			int g = Math.floorMod(state.getValue(GLYPH) + (player.isSecondaryUseActive() ? -1 : 1), Glyphs.COUNT);
			level.setBlock(pos, state.setValue(GLYPH, g), Block.UPDATE_ALL);
			level.playSound(null, pos, SoundEvents.DECORATED_POT_INSERT, SoundSource.BLOCKS, 0.8F, 0.8F + g * 0.05F);
		}
		return InteractionResult.SUCCESS;
	}
}
