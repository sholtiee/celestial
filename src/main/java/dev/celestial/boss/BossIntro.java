package dev.celestial.boss;

import dev.celestial.network.ShakePayload;
import java.util.Collection;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

/**
 * Постановка битв с боссами, общая для всех: титр с именем при пробуждении, титр «Фаза II/III» с названием фазы,
 * тряска камеры. Реплики в чат остаются в самих боссах.
 */
public final class BossIntro {
	private static final String[] ROMAN = {"I", "II", "III", "IV", "V"};

	private BossIntro() {}

	/** Пробуждение: имя босса крупно (цветом босса), подзаголовок-подсказка, сильная тряска всем в радиусе. */
	public static void awaken(ServerLevel level, BlockPos pos, String boss, ChatFormatting colour, double radius) {
		for (ServerPlayer p : level.getPlayers(p -> p.distanceToSqr(Vec3.atCenterOf(pos)) < radius * radius)) {
			title(p, Component.translatable("entity.celestial." + boss).withStyle(colour, ChatFormatting.BOLD),
				Component.translatable("boss.celestial." + boss + ".subtitle"), 70);
			shake(p, 2.5F, 30);
		}
	}

	/** Смена фазы: «Фаза II» и её название, тряска поменьше. */
	public static void phase(Collection<ServerPlayer> players, String boss, int phase, ChatFormatting colour) {
		for (ServerPlayer p : players) {
			title(p, Component.translatable("boss.celestial.phase", ROMAN[Math.min(phase, ROMAN.length) - 1]).withStyle(colour),
				Component.translatable("boss.celestial." + boss + ".phase" + phase + ".title").withStyle(ChatFormatting.ITALIC), 50);
			shake(p, 1.6F, 20);
		}
	}

	public static void title(ServerPlayer p, Component title, Component subtitle, int stay) {
		p.connection.send(new ClientboundSetTitlesAnimationPacket(10, stay, 20));
		p.connection.send(new ClientboundSetTitleTextPacket(title));
		p.connection.send(new ClientboundSetSubtitleTextPacket(subtitle));
	}

	public static void shake(ServerPlayer p, float strength, int ticks) {
		ServerPlayNetworking.send(p, new ShakePayload(strength, ticks));
	}
}
