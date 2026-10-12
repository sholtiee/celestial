package dev.celestial.block.puzzle.babel;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Глиняная плита с глифом: {@code glyph} — слово (см. {@link Glyphs#WORDS}), {@code script} — письмо. Неразрушима.
 * ПКМ пустой рукой — «знак незнаком»; Глиняная табличка в руке читает знак ({@link dev.celestial.item.ClayTabletItem}).
 */
public class BabelGlyphBlock extends Block implements dev.celestial.puzzle.PuzzleInteractive {
	public static final IntegerProperty GLYPH = IntegerProperty.create("glyph", 0, Glyphs.COUNT - 1);
	public static final IntegerProperty SCRIPT = IntegerProperty.create("script", 0, Glyphs.SCRIPTS - 1);

	public BabelGlyphBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(GLYPH, 0).setValue(SCRIPT, 0));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(GLYPH, SCRIPT);
	}

	/** С Глиняной табличкой в руке клик — чтение знака (предмет), а не поворот/подсказка. */
	@Override
	protected InteractionResult useItemOn(net.minecraft.world.item.ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
		net.minecraft.world.InteractionHand hand, BlockHitResult hit) {
		return stack.is(dev.celestial.registry.ModItems.CLAY_TABLET) ? InteractionResult.PASS : InteractionResult.TRY_WITH_EMPTY_HAND;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!level.isClientSide()) {
			player.sendOverlayMessage(Component.translatable(state.getValue(SCRIPT) == 0 ? "puzzle.celestial.babel.picture" : "puzzle.celestial.babel.unknown"));
		}
		return InteractionResult.SUCCESS;
	}
}
