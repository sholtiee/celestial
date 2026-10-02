package dev.celestial.world.portal;

import java.util.function.Predicate;
import java.util.function.Supplier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Описание портала между «домашним» миром и измерением мода.
 * frame — блок рамки, portal — блок завесы, activator — предмет, которым зажигают рамку,
 * groundInTarget — на чём можно ставить парный портал в целевом мире, platform — из чего строить площадку.
 */
public record PortalType(
	String id,
	Supplier<Block> frame,
	Supplier<Block> portal,
	Supplier<Item> activator,
	ResourceKey<Level> home,
	ResourceKey<Level> target,
	Predicate<BlockState> groundInTarget,
	Supplier<BlockState> platform,
	int fallbackY
) {
	public boolean isFrame(BlockState state) {
		return state.is(frame.get());
	}

	/** Куда ведёт портал из данного мира (или null, если портал здесь не работает). */
	public ResourceKey<Level> destinationFrom(ResourceKey<Level> current) {
		return current == target ? home : current == home ? target : null;
	}
}
