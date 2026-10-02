package dev.celestial.story;

import dev.celestial.registry.ModEffects;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;

/** Концовка: титры на экране, эпилог в чате и вечное Благословение. */
public final class Finale {
	private Finale() {}

	public static void play(ServerPlayer player) {
		player.connection.send(new ClientboundSetTitlesAnimationPacket(20, 120, 40));
		player.connection.send(new ClientboundSetTitleTextPacket(Component.translatable("story.celestial.finale.title")));
		player.connection.send(new ClientboundSetSubtitleTextPacket(Component.translatable("story.celestial.finale.subtitle")));
		for (int i = 1; i <= 5; i++) {
			player.sendSystemMessage(Component.translatable("story.celestial.epilogue." + i));
		}
		player.addEffect(new MobEffectInstance(ModEffects.BLESSING, MobEffectInstance.INFINITE_DURATION, 0, true, true, true));
	}
}
