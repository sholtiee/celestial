package dev.celestial.network;

import dev.celestial.Celestial;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Сервер → клиент: открыть экран машины (ПКМ пустой рукой) — какая машина, собрана ли, есть ли питание. */
public record MachinePayload(String machine, boolean complete, boolean powered) implements CustomPacketPayload {
	public static final Type<MachinePayload> TYPE = new Type<>(Celestial.id("machine"));
	public static final StreamCodec<ByteBuf, MachinePayload> CODEC = StreamCodec.composite(
		ByteBufCodecs.STRING_UTF8, MachinePayload::machine,
		ByteBufCodecs.BOOL, MachinePayload::complete,
		ByteBufCodecs.BOOL, MachinePayload::powered,
		MachinePayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
