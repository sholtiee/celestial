package dev.celestial.grace;

import dev.celestial.Celestial;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Клиент → сервер: изучить навык и сотворить заклинание. */
public final class GracePayloads {
	private GracePayloads() {}

	public record LearnSkill(String skill) implements CustomPacketPayload {
		public static final Type<LearnSkill> TYPE = new Type<>(Celestial.id("learn_skill"));
		public static final StreamCodec<ByteBuf, LearnSkill> CODEC = ByteBufCodecs.STRING_UTF8.map(LearnSkill::new, LearnSkill::skill);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	public record CastSpell(int spell) implements CustomPacketPayload {
		public static final Type<CastSpell> TYPE = new Type<>(Celestial.id("cast_spell"));
		public static final StreamCodec<ByteBuf, CastSpell> CODEC = ByteBufCodecs.VAR_INT.map(CastSpell::new, CastSpell::spell);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}
}
