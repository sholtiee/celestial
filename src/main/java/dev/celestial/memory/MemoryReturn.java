package dev.celestial.memory;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;

/** Куда вернуть странника из воспоминания: мир, точка, взгляд, режим игры; якорь, сцена и «впервые ли» — для последствий (сохраняется на случай выхода из игры). */
public record MemoryReturn(String dimension, double x, double y, double z, float yaw, float pitch, String gameMode, BlockPos anchor, String scene,
	boolean first) {
	public static final Codec<MemoryReturn> CODEC = RecordCodecBuilder.create(i -> i.group(
		Codec.STRING.fieldOf("dimension").forGetter(MemoryReturn::dimension),
		Codec.DOUBLE.fieldOf("x").forGetter(MemoryReturn::x),
		Codec.DOUBLE.fieldOf("y").forGetter(MemoryReturn::y),
		Codec.DOUBLE.fieldOf("z").forGetter(MemoryReturn::z),
		Codec.FLOAT.fieldOf("yaw").forGetter(MemoryReturn::yaw),
		Codec.FLOAT.fieldOf("pitch").forGetter(MemoryReturn::pitch),
		Codec.STRING.fieldOf("game_mode").forGetter(MemoryReturn::gameMode),
		BlockPos.CODEC.fieldOf("anchor").forGetter(MemoryReturn::anchor),
		Codec.STRING.fieldOf("scene").forGetter(MemoryReturn::scene),
		Codec.BOOL.optionalFieldOf("first", false).forGetter(MemoryReturn::first)
	).apply(i, MemoryReturn::new));
}
