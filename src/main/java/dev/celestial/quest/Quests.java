package dev.celestial.quest;

import dev.celestial.data.CelestialData;
import dev.celestial.data.PlayerData;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/** Логика поручений: доска, прогресс (убийства, посещение построек), сдача и награды. */
public final class Quests {
	public static final int MAX_ACTIVE = 3;

	private Quests() {}

	public static void init() {
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (source.getEntity() instanceof ServerPlayer player) {
				String id = BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString();
				advance(player, Quest.Type.KILL, id, 1);
			}
		});
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 100 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				for (Quest q : active(player)) {
					if (q.type() == Quest.Type.EXPLORE && !q.isComplete() && inside(player, q.target())) {
						advance(player, Quest.Type.EXPLORE, q.target(), 1);
					}
				}
			}
		});
	}

	/** Маркер «сдано сегодня» лежит в том же списке: DONE;день;ТИП;цель — по нему поручение нельзя взять дважды за день. */
	private static final String DONE = "DONE;";

	private static long today(Player player) {
		return player.level().getOverworldClockTime() / 24000L;
	}

	public static List<Quest> active(Player player) {
		return CelestialData.get(player).quests().stream().filter(s -> !s.startsWith(DONE)).map(Quest::decode).toList();
	}

	/** Выполнено ли такое поручение сегодня (повтор после сдачи давал бесконечные награды). */
	public static boolean doneToday(Player player, Quest q) {
		String key = DONE + today(player) + ";" + q.type().name() + ";" + q.target();
		return CelestialData.get(player).quests().contains(key);
	}

	private static void save(Player player, List<Quest> quests) {
		long day = today(player);
		List<String> out = new ArrayList<>(quests.stream().map(Quest::encode).toList());
		// маркеры прошлых дней отбрасываем
		CelestialData.get(player).quests().stream().filter(s -> s.startsWith(DONE + day + ";")).forEach(out::add);
		CelestialData.update(player, d -> d.withQuests(out));
	}

	private static void markDone(Player player, Quest q) {
		List<String> now = new ArrayList<>(CelestialData.get(player).quests());
		now.add(DONE + today(player) + ";" + q.type().name() + ";" + q.target());
		CelestialData.update(player, d -> d.withQuests(now));
	}

	private static boolean inside(ServerPlayer player, String structure) {
		ServerLevel level = player.level();
		var registry = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);
		var holder = registry.get(ResourceKey.create(Registries.STRUCTURE, Identifier.parse(structure)));
		return holder.isPresent() && level.structureManager().getStructureWithPieceAt(player.blockPosition(), s -> s.equals(holder.get())).isValid();
	}

	/** Прогресс по убийствам/исследованию; по завершении поручение сразу награждается. */
	public static void advance(ServerPlayer player, Quest.Type type, String target, int amount) {
		List<Quest> list = new ArrayList<>(active(player));
		boolean changed = false;
		for (int i = 0; i < list.size(); i++) {
			Quest q = list.get(i);
			if (q.type() == type && q.target().equals(target) && !q.isComplete()) {
				Quest updated = q.withProgress(q.progress() + amount);
				list.set(i, updated);
				changed = true;
				if (updated.isComplete()) {
					markDone(player, updated);
					reward(player, updated);
					list.remove(i);
					i--;
				} else {
					player.sendOverlayMessage(updated.describe());
				}
			}
		}
		if (changed) {
			save(player, list);
		}
	}

	private static void reward(ServerPlayer player, Quest q) {
		Item item = BuiltInRegistries.ITEM.getValue(Identifier.parse(q.reward()));
		ItemStack stack = new ItemStack(item, q.rewardCount());
		if (!player.getInventory().add(stack)) {
			player.spawnAtLocation(player.level(), stack);
		}
		CelestialData.update(player, d -> d.withReputation(d.reputation() + q.reputation()).withCodex("quests"));
		player.level().playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.8F, 1.4F);
		player.sendSystemMessage(Component.translatable("quest.celestial.done").withStyle(ChatFormatting.GREEN).append(" ").append(q.describeReward()));
	}

	/** Доска: показать активные и сегодняшние поручения кликабельным списком. */
	public static void showBoard(ServerPlayer player, BlockPos board) {
		long day = player.level().getOverworldClockTime() / 24000L;
		player.sendSystemMessage(Component.translatable("quest.celestial.board.header", CelestialData.get(player).reputation()).withStyle(ChatFormatting.GOLD));
		List<Quest> mine = active(player);
		for (int i = 0; i < mine.size(); i++) {
			Quest q = mine.get(i);
			var line = Component.literal(" ◆ ").withStyle(ChatFormatting.YELLOW).append(q.describe().copy().withStyle(ChatFormatting.WHITE));
			if (q.type() == Quest.Type.BRING) {
				line.append(Component.literal("  ")).append(Component.translatable("quest.celestial.turn_in").withStyle(s -> s.withColor(ChatFormatting.GREEN)
					.withClickEvent(new ClickEvent.RunCommand("/celestial quest turnin " + board.getX() + " " + board.getY() + " " + board.getZ()))));
			}
			player.sendSystemMessage(line);
		}
		List<Quest> offers = QuestPool.offers(day, board);
		for (int i = 0; i < offers.size(); i++) {
			Quest q = offers.get(i);
			boolean taken = mine.stream().anyMatch(q::sameAs) || doneToday(player, q);
			var line = Component.literal(" ✦ ").withStyle(ChatFormatting.AQUA).append(q.describe().copy().withStyle(ChatFormatting.GRAY))
				.append(" ").append(q.describeReward().copy().withStyle(ChatFormatting.DARK_AQUA));
			if (!taken) {
				int index = i;
				line.append(Component.literal("  ")).append(Component.translatable("quest.celestial.take").withStyle(s -> s.withColor(ChatFormatting.GREEN)
					.withClickEvent(new ClickEvent.RunCommand("/celestial quest take " + board.getX() + " " + board.getY() + " " + board.getZ() + " " + index))
					.withHoverEvent(new HoverEvent.ShowText(Component.translatable("quest.celestial.take_hint")))));
			}
			player.sendSystemMessage(line);
		}
	}

	public static int take(ServerPlayer player, BlockPos board, int index) {
		if (!nearBoard(player, board)) {
			return 0;
		}
		List<Quest> offers = QuestPool.offers(player.level().getOverworldClockTime() / 24000L, board);
		List<Quest> mine = new ArrayList<>(active(player));
		if (index < 0 || index >= offers.size() || mine.stream().anyMatch(offers.get(index)::sameAs)) {
			return 0;
		}
		if (doneToday(player, offers.get(index))) {
			player.sendOverlayMessage(Component.translatable("quest.celestial.done_today"));
			return 0;
		}
		if (mine.size() >= MAX_ACTIVE) {
			player.sendOverlayMessage(Component.translatable("quest.celestial.too_many"));
			return 0;
		}
		mine.add(offers.get(index));
		save(player, mine);
		player.sendOverlayMessage(Component.translatable("quest.celestial.taken"));
		return 1;
	}

	/** Сдать предметы по всем поручениям «принеси». */
	public static int turnIn(ServerPlayer player, BlockPos board) {
		if (!nearBoard(player, board)) {
			return 0;
		}
		int done = 0;
		for (Quest q : active(player)) {
			if (q.type() != Quest.Type.BRING) {
				continue;
			}
			Item item = BuiltInRegistries.ITEM.getValue(Identifier.parse(q.target()));
			int have = player.getInventory().countItem(item);
			int give = Math.min(have, q.need() - q.progress());
			if (give <= 0) {
				continue;
			}
			int left = give;
			var inv = player.getInventory();
			for (int i = 0; i < inv.getContainerSize() && left > 0; i++) {
				ItemStack s = inv.getItem(i);
				if (s.is(item)) {
					int n = Math.min(left, s.getCount());
					s.shrink(n);
					left -= n;
				}
			}
			advance(player, Quest.Type.BRING, q.target(), give);
			done++;
		}
		if (done == 0) {
			player.sendOverlayMessage(Component.translatable("quest.celestial.nothing"));
		}
		return done;
	}

	private static boolean nearBoard(ServerPlayer player, BlockPos board) {
		return player.blockPosition().closerThan(board, 6) && player.level().getBlockState(board).is(dev.celestial.registry.ModBlocks.QUEST_BOARD);
	}
}
