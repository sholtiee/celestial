package dev.celestial.network;

import dev.celestial.Celestial;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Клиент → сервер: «Пережить снова» — войти в уже пережитое воспоминание из Летописи. */
public record ReplayMemoryPayload(String scene) implements CustomPacketPayload {
	public static final Type<ReplayMemoryPayload> TYPE = new Type<>(Celestial.id("replay_memory"));
	public static final StreamCodec<ByteBuf, ReplayMemoryPayload> CODEC = ByteBufCodecs.STRING_UTF8.map(ReplayMemoryPayload::new, ReplayMemoryPayload::scene);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
