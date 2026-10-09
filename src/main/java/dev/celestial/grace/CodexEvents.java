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
		// «Книга Имён» (docs/LORE.md §4): как Адам нарекал имена — присесть и коснуться существа мода пустой рукой, и оно записано без убийства
		net.fabricmc.fabric.api.event.player.UseEntityCallback.EVENT.register((player, world, hand, entity, hit) -> {
			if (!world.isClientSide() && player instanceof ServerPlayer sp && sp.isShiftKeyDown() && hand == net.minecraft.world.InteractionHand.MAIN_HAND
				&& sp.getMainHandItem().isEmpty() && !dev.celestial.memory.Memories.inMemory(sp) && name(sp, entity)) {  // в воспоминании — движок сцен
				return net.minecraft.world.InteractionResult.SUCCESS;
			}
			return net.minecraft.world.InteractionResult.PASS;
		});
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 100 != 50) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				if (player.level().dimension().identifier().getPath().equals("frozen_halls")) {
					dev.celestial.lore.Lore.unlock(player, "firmament_waters");  // «Воды над твердью»: приход в Ледяные Чертоги
				}
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

	/** Наречь существо мода: записать в бестиарий без убийства. true — запись новая. */
	public static boolean name(ServerPlayer sp, net.minecraft.world.entity.Entity entity) {
		var key = BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType());
		if (entity instanceof net.minecraft.world.entity.LivingEntity && key.getNamespace().equals("celestial") && !key.getPath().startsWith("memory_")
			&& !CelestialData.get(sp).knows("mob:" + key.getPath())) {
			unlock(sp, "mob:" + key.getPath(), entity.getType().getDescription());
			sp.level().sendParticles(net.minecraft.core.particles.ParticleTypes.END_ROD, entity.getX(), entity.getY(1.0), entity.getZ(), 12, 0.3, 0.3, 0.3, 0.02);
			return true;
		}
		return false;
	}

	private static void unlock(ServerPlayer player, String entry, Component name) {
		if (!CelestialData.get(player).knows(entry)) {
			CelestialData.update(player, d -> d.withCodex(entry));
			player.sendOverlayMessage(Component.translatable("codex.celestial.new_entry", name));
			if (entry.startsWith("mob:")) {
				dev.celestial.lore.Lore.check(player);  // «Книга Имён»: чем больше существ записано, тем ближе лист «Имена» и достижение
			}
		}
	}
}
