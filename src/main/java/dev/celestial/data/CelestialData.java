package dev.celestial.data;

import dev.celestial.Celestial;
import dev.celestial.network.CelestialNetwork;
import java.util.function.UnaryOperator;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentSyncPredicate;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.player.Player;

/** Точка доступа к данным мода: прогресс игрока (синхронизируется с его клиентом) и состояние мира. */
public final class CelestialData {
	public static final AttachmentType<PlayerData> PLAYER = AttachmentRegistry.<PlayerData>builder()
		.persistent(PlayerData.CODEC)
		.copyOnDeath()
		.initializer(() -> PlayerData.EMPTY)
		.syncWith(PlayerData.STREAM_CODEC, AttachmentSyncPredicate.targetOnly())
		.buildAndRegister(Celestial.id("player_data"));

	public static final AttachmentType<WorldState> WORLD = AttachmentRegistry.<WorldState>builder()
		.persistent(WorldState.CODEC)
		.initializer(() -> WorldState.INITIAL)
		.buildAndRegister(Celestial.id("world_state"));

	public static final AttachmentType<BeaconNetwork> BEACONS = AttachmentRegistry.<BeaconNetwork>builder()
		.persistent(BeaconNetwork.CODEC)
		.initializer(() -> BeaconNetwork.EMPTY)
		.buildAndRegister(Celestial.id("beacon_network"));

	private CelestialData() {}

	public static BeaconNetwork beacons(MinecraftServer server) {
		return server.overworld().getAttachedOrCreate(BEACONS);
	}

	public static void updateBeacons(MinecraftServer server, UnaryOperator<BeaconNetwork> change) {
		server.overworld().setAttached(BEACONS, change.apply(beacons(server)));
	}

	public static void init() {
	}

	public static PlayerData get(Player player) {
		return player.getAttachedOrCreate(PLAYER);
	}

	public static PlayerData update(Player player, UnaryOperator<PlayerData> change) {
		PlayerData updated = change.apply(get(player));
		player.setAttached(PLAYER, updated);
		return updated;
	}

	public static WorldState world(MinecraftServer server) {
		return server.overworld().getAttachedOrCreate(WORLD);
	}

	/** Меняет состояние мира и рассылает игрокам новую стадию Угасания. */
	public static WorldState updateWorld(MinecraftServer server, UnaryOperator<WorldState> change) {
		ServerLevel overworld = server.overworld();
		WorldState before = world(server);
		WorldState after = change.apply(before);
		overworld.setAttached(WORLD, after);
		if (after.fading() != before.fading() || after.act() != before.act()) {
			CelestialNetwork.broadcastWorld(server, after);
		}
		return after;
	}
}
