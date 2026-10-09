package dev.celestial.network;

import dev.celestial.Celestial;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Сервер → клиент: странник в воспоминании (золотая плёнка памяти, вспышка входа/выхода) и насколько «померк свет» в сцене (0..1). */
public record MemoryOverlayPayload(boolean active, float dim) implements CustomPacketPayload {
	public static final Type<MemoryOverlayPayload> TYPE = new Type<>(Celestial.id("memory_overlay"));
	public static final StreamCodec<ByteBuf, MemoryOverlayPayload> CODEC = StreamCodec.composite(
		ByteBufCodecs.BOOL, MemoryOverlayPayload::active,
		ByteBufCodecs.FLOAT, MemoryOverlayPayload::dim,
		MemoryOverlayPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
