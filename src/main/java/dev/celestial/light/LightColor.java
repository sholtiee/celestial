package dev.celestial.light;

import net.minecraft.util.StringRepresentable;

/** Цвет луча. Белый луч Призма раскладывает на красный, зелёный и синий. */
public enum LightColor implements StringRepresentable {
	WHITE("white", 0xFFF6D8),
	RED("red", 0xFF5A4A),
	GREEN("green", 0x6CFF7A),
	BLUE("blue", 0x5AA8FF);

	private final String name;
	public final int rgb;

	LightColor(String name, int rgb) {
		this.name = name;
		this.rgb = rgb;
	}

	@Override
	public String getSerializedName() {
		return name;
	}
}
