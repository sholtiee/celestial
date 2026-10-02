package dev.celestial.network;

import dev.celestial.Celestial;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Сервер → клиент: стадия Угасания и акт (для неба, HUD и Кодекса). */
public record WorldStatePayload(int fading, int act, boolean fadingEnabled) implements CustomPacketPayload {
	public static final Type<WorldStatePayload> TYPE = new Type<>(Celestial.id("world_state"));
	public static final StreamCodec<ByteBuf, WorldStatePayload> CODEC = StreamCodec.composite(
		ByteBufCodecs.VAR_INT, WorldStatePayload::fading,
		ByteBufCodecs.VAR_INT, WorldStatePayload::act,
		ByteBufCodecs.BOOL, WorldStatePayload::fadingEnabled,
		WorldStatePayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
