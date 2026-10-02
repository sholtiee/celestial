package dev.celestial.grace;

import dev.celestial.data.CelestialData;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.levelgen.structure.Structure;

/** Кодекс заполняется сам: бестиарий — при победе над существом мода, места — при посещении построек. */
public final class CodexEvents {
	private static final TagKey<Structure> PLACES = TagKey.create(Registries.STRUCTURE, dev.celestial.Celestial.id("codex_places"));

	private CodexEvents() {}

	public static void init() {
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (source.getEntity() instanceof ServerPlayer player) {
				var key = BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType());
				if (key.getNamespace().equals("celestial")) {
					unlock(player, "mob:" + key.getPath(), entity.getType().getDescription());
				}
			}
		});
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 100 != 50) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				var start = player.level().structureManager().getStructureWithPieceAt(player.blockPosition(), PLACES);
				if (start.isValid()) {
					var key = player.level().registryAccess().lookupOrThrow(Registries.STRUCTURE).getKey(start.getStructure());
					if (key != null) {
						unlock(player, "place:" + key.getPath(), Component.translatable("structure.celestial." + key.getPath()));
					}
				}
			}
		});
	}

	private static void unlock(ServerPlayer player, String entry, Component name) {
		if (!CelestialData.get(player).knows(entry)) {
			CelestialData.update(player, d -> d.withCodex(entry));
			player.sendOverlayMessage(Component.translatable("codex.celestial.new_entry", name));
		}
	}
}
