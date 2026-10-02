package dev.celestial.item;

import dev.celestial.story.StoryEvents;
import dev.celestial.world.portal.PortalActivation;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.context.UseOnContext;

/** Сердце Пустоты: зажигает рамку из светлого камня, сам не расходуется. */
public class VoidHeartItem extends Item {
	public VoidHeartItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult useOn(UseOnContext context) {
		return PortalActivation.tryActivate(context, () -> {
			if (context.getPlayer() != null) {
				StoryEvents.onHeavenPortalLit(context.getPlayer());
			}
		});
	}
}
