package dev.celestial.block.light;

import net.minecraft.world.level.block.state.BlockState;

/** Блоки, которые Камертон поворачивает (зеркала, призмы, линзы, звёздные диски). */
public interface Rotatable {
	BlockState rotateWithFork(BlockState state);
}
