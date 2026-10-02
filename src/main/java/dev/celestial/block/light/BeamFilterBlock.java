package dev.celestial.block.light;

import dev.celestial.light.LightColor;
import net.minecraft.world.level.block.Block;
import org.jspecify.annotations.Nullable;

/** Цветной фильтр: белый луч окрашивает, свой цвет пропускает, чужой — гасит. */
public class BeamFilterBlock extends Block {
	private final LightColor color;

	public BeamFilterBlock(LightColor color, Properties properties) {
		super(properties);
		this.color = color;
	}

	public @Nullable LightColor filter(LightColor incoming) {
		return incoming == LightColor.WHITE || incoming == color ? color : null;
	}
}
