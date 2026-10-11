package dev.celestial.story;

import dev.celestial.boss.Faceless;
import dev.celestial.data.CelestialData;
import dev.celestial.network.EndingPayloads;
import dev.celestial.registry.ModItems;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import org.jspecify.annotations.Nullable;

/**
 * Концовки Саги у повергнутого Безликого (LORE §6, HANDOFF «Волна 0.6»).
 * «Возжечь» — отдать свет миру: Угасание выключено навсегда, игрок — Хранитель. «Поглотить» — взять свет себе: игрок — новый Серафим,
 * в Верхнем мире вечная ночь. «Имя» — тайная (вся Летопись): назвать его прежнее имя (O5 шаг 4c).
 * Выбор — экран у клиента; сервер проверяет, что рядом повергнутый Безликий. Итог пишется в мир (флаги) и каждому участнику (Кодекс).
 */
public final class Endings {
	public static final String KINDLE = "kindle";
	public static final String CONSUME = "consume";
	public static final String NAME = "name";

	private Endings() {}

	public static void init() {
		PayloadTypeRegistry.clientboundPlay().register(EndingPayloads.Open.TYPE, EndingPayloads.Open.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(EndingPayloads.Choose.TYPE, EndingPayloads.Choose.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(EndingPayloads.Choose.TYPE, (payload, ctx) -> choose(ctx.player(), payload.choice()));
		net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(Endings::tick);
	}

	/** Тайная концовка доступна: собраны все книги Летописи («Книга Жизни»). */
	public static boolean nameAllowed(ServerPlayer p) {
		return dev.celestial.lore.Lore.allBooksComplete(p);
	}

	public static void offer(ServerPlayer p, Faceless boss) {
		ServerPlayNetworking.send(p, new EndingPayloads.Open(nameAllowed(p)));
	}

	/** Выбор с экрана; также команда /celestial ending <выбор> для сценариев. */
	public static boolean choose(ServerPlayer p, String choice) {
		ServerLevel level = p.level();
		Faceless boss = nearestDefeated(level, p);
		if (boss == null) {
			return false;
		}
		switch (choice) {
			case KINDLE -> apply(level, boss, KINDLE);
			case CONSUME -> apply(level, boss, CONSUME);
			case NAME -> {
				if (!nameAllowed(p)) {
					p.sendOverlayMessage(Component.translatable("ending.celestial.name.locked"));
					return false;
				}
				p.sendOverlayMessage(Component.translatable("ending.celestial.name.soon"));  // O5 шаг 4c
				return false;
			}
			default -> {
				return false;
			}
		}
		return true;
	}

	private static @Nullable Faceless nearestDefeated(ServerLevel level, ServerPlayer p) {
		return level.getEntitiesOfClass(Faceless.class, p.getBoundingBox().inflate(12), Faceless::defeated).stream().findFirst().orElse(null);
	}

	private static void apply(ServerLevel level, Faceless boss, String ending) {
		boolean light = ending.equals(KINDLE);
		MinecraftServer server = level.getServer();
		for (ServerPlayer p : boss.fighters(level)) {
			CelestialData.update(p, d -> d.withGrace(d.grace() + 10).withCodex("ending:" + ending));
			if (!light) {
				ItemStack wings = new ItemStack(ModItems.SERAPH_WINGS);
				if (!p.getInventory().add(wings)) {
					p.spawnAtLocation(level, wings);
				}
			}
			dev.celestial.boss.BossIntro.title(p, Component.translatable("ending.celestial." + ending + ".title")
					.withStyle(light ? ChatFormatting.GOLD : ChatFormatting.DARK_PURPLE, ChatFormatting.BOLD),
				Component.translatable("ending.celestial." + ending + ".subtitle").withStyle(ChatFormatting.ITALIC), 140);
			for (int i = 1; i <= 4; i++) {
				p.sendSystemMessage(Component.translatable("ending.celestial." + ending + "." + i));
			}
			(light ? Story.KINDLED : Story.CONSUMED).grant(p);
		}
		CelestialData.updateWorld(server, w -> w.withAct(Math.max(5, w.act())).withFading(0).withFlag("act5_done").withFlag("ending_" + ending));
		server.getPlayerList().getPlayers().forEach(StoryEvents::syncActs);
		boss.release(level, light);
	}

	/** Для сценариев: снять концовки с мира и игрока (флаги, записи Кодекса), отпустить часы. */
	public static void reset(ServerPlayer p) {
		MinecraftServer server = p.level().getServer();
		CelestialData.updateWorld(server, w -> w.withoutFlag("ending_" + KINDLE).withoutFlag("ending_" + CONSUME).withoutFlag("ending_" + NAME));
		CelestialData.update(p, d -> d.withoutCodex("ending:" + KINDLE).withoutCodex("ending:" + CONSUME).withoutCodex("ending:" + NAME));
		ServerLevel overworld = server.overworld();
		var clock = overworld.registryAccess().lookupOrThrow(net.minecraft.core.registries.Registries.WORLD_CLOCK)
			.getOrThrow(net.minecraft.world.clock.WorldClocks.OVERWORLD);
		overworld.clockManager().setPaused(clock, false);
	}

	/** «Поглотить»: в Верхнем мире вечная ночь — часы мира стоят на полуночи. */
	private static void tick(MinecraftServer server) {
		if (server.getTickCount() % 40 != 0 || !CelestialData.world(server).has("ending_consume")) {
			return;
		}
		ServerLevel overworld = server.overworld();
		var clock = overworld.registryAccess().lookupOrThrow(net.minecraft.core.registries.Registries.WORLD_CLOCK)
			.getOrThrow(net.minecraft.world.clock.WorldClocks.OVERWORLD);
		var manager = overworld.clockManager();
		long t = manager.getInstance(clock).totalTicks();
		if (t % 24000L != 18000L) {
			manager.setTotalTicks(clock, t - t % 24000L + 18000L);
		}
		manager.setPaused(clock, true);
	}
}
