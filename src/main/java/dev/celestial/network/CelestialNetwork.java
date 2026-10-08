package dev.celestial.network;

import dev.celestial.data.CelestialData;
import dev.celestial.data.WorldState;
import dev.celestial.registry.ModGameRules;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

public final class CelestialNetwork {
	/** Последнее разосланное значение правила celestial:fading (null — ещё не знаем). */
	private static Boolean lastFadingRule;

	private CelestialNetwork() {}

	public static void init() {
		PayloadTypeRegistry.clientboundPlay().register(WorldStatePayload.TYPE, WorldStatePayload.CODEC);
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) ->
			server.execute(() -> sendWorld(handler.player, CelestialData.world(server))));
		// правило меняют командой /gamerule, событий у него нет — сверяем раз в 2 с и рассылаем, если изменилось (BUG-037)
		net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 40 != 0) {
				return;
			}
			boolean now = server.overworld().getGameRules().get(ModGameRules.FADING);
			if (lastFadingRule != null && lastFadingRule != now) {
				broadcastWorld(server, CelestialData.world(server));
			}
			lastFadingRule = now;
		});
		net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents.SERVER_STOPPED.register(server -> lastFadingRule = null);
	}

	public static void sendWorld(ServerPlayer player, WorldState state) {
		boolean enabled = player.level().getServer().overworld().getGameRules().get(ModGameRules.FADING);
		ServerPlayNetworking.send(player, new WorldStatePayload(state.fading(), state.act(), enabled));
	}

	public static void broadcastWorld(MinecraftServer server, WorldState state) {
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			sendWorld(player, state);
		}
	}
}
