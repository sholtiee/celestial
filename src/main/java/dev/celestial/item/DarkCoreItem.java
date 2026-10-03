package dev.celestial.item;

import dev.celestial.world.portal.PortalActivation;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.context.UseOnContext;

/** Тёмное Ядро: зажигает рамку из кирпичей морозного камня — путь в Ледяные Чертоги. Само не расходуется. */
public class DarkCoreItem extends Item {
	public DarkCoreItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult useOn(UseOnContext context) {
		return PortalActivation.tryActivate(context, () -> {
			if (context.getPlayer() != null) {
				context.getPlayer().sendSystemMessage(Component.translatable("story.celestial.frozen_portal_lit"));
			}
		});
	}
}
