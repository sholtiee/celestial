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
	private CelestialNetwork() {}

	public static void init() {
		PayloadTypeRegistry.clientboundPlay().register(WorldStatePayload.TYPE, WorldStatePayload.CODEC);
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) ->
			server.execute(() -> sendWorld(handler.player, CelestialData.world(server))));
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
