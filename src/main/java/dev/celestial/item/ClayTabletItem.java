package dev.celestial.item;

import dev.celestial.block.puzzle.babel.BabelGlyphBlock;
import dev.celestial.block.puzzle.babel.GlyphWheelBlock;
import dev.celestial.block.puzzle.babel.Glyphs;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Глиняная табличка (Книга Башни): на ней все четыре письма Вавилона рядом. ПКМ по глифу или колесу замка —
 * прочесть знак. Добывается в эпизоде «Вавилон» у подножия башни.
 */
public class ClayTabletItem extends Item {
	public ClayTabletItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult useOn(UseOnContext context) {
		BlockState state = context.getLevel().getBlockState(context.getClickedPos());
		int glyph;
		if (state.getBlock() instanceof BabelGlyphBlock) {
			glyph = state.getValue(BabelGlyphBlock.GLYPH);
		} else if (state.getBlock() instanceof GlyphWheelBlock) {
			glyph = state.getValue(GlyphWheelBlock.GLYPH);
		} else {
			return InteractionResult.PASS;
		}
		if (!context.getLevel().isClientSide() && context.getPlayer() != null) {
			context.getPlayer().sendOverlayMessage(Component.translatable("item.celestial.clay_tablet.reads",
				Component.translatable("glyph.celestial." + Glyphs.WORDS[glyph]).withStyle(ChatFormatting.GOLD)));
			context.getLevel().playSound(null, context.getClickedPos(), SoundEvents.BOOK_PAGE_TURN, SoundSource.PLAYERS, 1.0F, 0.8F);
		}
		return InteractionResult.SUCCESS;
	}
}
