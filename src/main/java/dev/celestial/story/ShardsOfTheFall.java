package dev.celestial.story;

import dev.celestial.data.CelestialData;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;

/**
 * «Осколки падения» (LORE §5c, S3.7): после смерти босса каждый участник через ~{@link #DELAY} тиков сам проваливается в короткий
 * Отблеск глазами побеждённого (Серафим, Пожиратель, Архонт) — один раз; если пока нельзя (бой, падение), пробует снова до минуты.
 */
public final class ShardsOfTheFall {
	private static final int DELAY = 160;
	private static final int GIVE_UP = 1200;

	private record Pending(UUID player, String scene, int[] ticks) {}

	private static final List<Pending> PENDING = new ArrayList<>();

	private ShardsOfTheFall() {}

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(ShardsOfTheFall::tick);
	}

	/** Босс пал: всем участникам рядом — Отблеск {@code scene} (если ещё не пережит). */
	public static void schedule(ServerLevel level, LivingEntity boss, String scene) {
		for (ServerPlayer p : level.getPlayers(p -> p.distanceToSqr(boss) < 96 * 96 && !p.isSpectator())) {
			if (!CelestialData.get(p).knows("memory:" + scene)) {
				PENDING.add(new Pending(p.getUUID(), scene, new int[] {0}));
			}
		}
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Pending> it = PENDING.iterator(); it.hasNext(); ) {
			Pending pd = it.next();
			int t = ++pd.ticks()[0];
			ServerPlayer p = server.getPlayerList().getPlayer(pd.player());
			if (p == null || t > GIVE_UP || CelestialData.get(p).knows("memory:" + pd.scene())) {
				it.remove();
				continue;
			}
			if (t >= DELAY && t % 40 == 0 && p.isAlive() && p.onGround()
				&& dev.celestial.memory.Memories.tryEnter(p, pd.scene(), p.blockPosition())) {
				it.remove();
			}
		}
	}
}
