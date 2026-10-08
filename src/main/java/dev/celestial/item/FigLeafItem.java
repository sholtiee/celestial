package dev.celestial.item;

import dev.celestial.eden.Exile;
import dev.celestial.registry.ModEffects;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** Лист смоковницы (Быт. 3:7): прикрывает изгнанника, снимая «Изгнание». */
public class FigLeafItem extends Item {
	public FigLeafItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		if (!Exile.isExiled(player)) {
			if (!level.isClientSide()) {
				player.sendOverlayMessage(Component.translatable("eden.celestial.leaf.nothing"));
			}
			return InteractionResult.FAIL;
		}
		if (!level.isClientSide()) {
			player.removeEffect(ModEffects.EXILE);
			player.sendOverlayMessage(Component.translatable("eden.celestial.leaf.covered"));
			stack.consume(1, player);
		}
		return InteractionResult.SUCCESS;
	}
}
