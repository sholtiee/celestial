package dev.celestial.network;

import dev.celestial.Celestial;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Выбор концовки у повергнутого Безликого. */
public final class EndingPayloads {
	private EndingPayloads() {}

	/** Сервер → клиент: открыть экран выбора; nameAllowed — доступна ли тайная концовка «Имя» (вся Летопись собрана). */
	public record Open(boolean nameAllowed) implements CustomPacketPayload {
		public static final Type<Open> TYPE = new Type<>(Celestial.id("ending_open"));
		public static final StreamCodec<ByteBuf, Open> CODEC = ByteBufCodecs.BOOL.map(Open::new, Open::nameAllowed);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Клиент → сервер: выбранная концовка (kindle, consume, name). */
	public record Choose(String choice) implements CustomPacketPayload {
		public static final Type<Choose> TYPE = new Type<>(Celestial.id("ending_choose"));
		public static final StreamCodec<ByteBuf, Choose> CODEC = ByteBufCodecs.STRING_UTF8.map(Choose::new, Choose::choice);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}
}
