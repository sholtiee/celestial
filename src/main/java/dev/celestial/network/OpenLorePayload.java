package dev.celestial.network;

import dev.celestial.Celestial;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Сервер → клиент: открыть Кодекс на листе Летописи (после чтения свитка или скрижали). */
public record OpenLorePayload(String sheet) implements CustomPacketPayload {
	public static final Type<OpenLorePayload> TYPE = new Type<>(Celestial.id("open_lore"));
	public static final StreamCodec<RegistryFriendlyByteBuf, OpenLorePayload> CODEC = StreamCodec.composite(
		ByteBufCodecs.STRING_UTF8, OpenLorePayload::sheet,
		OpenLorePayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
