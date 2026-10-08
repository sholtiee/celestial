package dev.celestial.network;

import dev.celestial.Celestial;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Сервер → клиент: тряска камеры (сила в градусах, длительность в тиках) — пробуждение и смена фазы босса, удары. */
public record ShakePayload(float strength, int ticks) implements CustomPacketPayload {
	public static final Type<ShakePayload> TYPE = new Type<>(Celestial.id("shake"));
	public static final StreamCodec<ByteBuf, ShakePayload> CODEC = StreamCodec.composite(
		ByteBufCodecs.FLOAT, ShakePayload::strength,
		ByteBufCodecs.VAR_INT, ShakePayload::ticks,
		ShakePayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
