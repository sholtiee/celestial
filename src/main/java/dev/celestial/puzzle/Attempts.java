package dev.celestial.puzzle;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;

/**
 * Штраф за неверные ответы: после каждой ошибки загадка закрыта для этого игрока на 20 с, и срок удваивается (до 10 минут).
 * Без этого рунный пьедестал решался перебором всех предметов инвентаря за минуту.
 */
public final class Attempts {
	private static final long BASE_TICKS = 400;
	private static final long MAX_TICKS = 12000;

	private record State(int fails, long until) {}

	private static final Map<String, State> STATES = new HashMap<>();

	private Attempts() {}

	public static void init() {
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> STATES.clear());  // не протекать между мирами одиночной игры
	}

	private static String key(ServerLevel level, BlockPos pos, Player player) {
		return level.dimension().identifier() + "|" + pos.asLong() + "|" + player.getUUID();
	}

	/** Секунд до конца блокировки, 0 — можно отвечать. */
	public static int lockedSeconds(ServerLevel level, BlockPos pos, Player player) {
		State s = STATES.get(key(level, pos, player));
		if (s == null) {
			return 0;
		}
		long left = s.until() - level.getGameTime();
		return left > 0 ? (int) Math.ceil(left / 20.0) : 0;
	}

	/** Записать ошибку: звук, частицы, сообщение с временем блокировки. */
	public static void fail(ServerLevel level, BlockPos pos, Player player, Component message) {
		String k = key(level, pos, player);
		State old = STATES.get(k);
		int fails = old == null ? 1 : old.fails() + 1;
		long lock = Math.min(MAX_TICKS, BASE_TICKS << Math.min(fails - 1, 10));
		STATES.put(k, new State(fails, level.getGameTime() + lock));
		level.playSound(null, pos, SoundEvents.NOTE_BLOCK_BASS.value(), SoundSource.BLOCKS, 1.0F, 0.5F);
		level.sendParticles(net.minecraft.core.particles.ParticleTypes.SMOKE, pos.getX() + 0.5, pos.getY() + 1.1, pos.getZ() + 0.5, 12, 0.3, 0.2, 0.3, 0.02);
		player.sendOverlayMessage(Component.translatable("puzzle.celestial.locked", message, (int) (lock / 20)));
	}

	public static void reset(ServerLevel level, BlockPos pos, Player player) {
		STATES.remove(key(level, pos, player));
	}
}
