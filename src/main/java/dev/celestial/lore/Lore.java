package dev.celestial.lore;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import dev.celestial.data.CelestialData;
import dev.celestial.data.PlayerData;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;

/**
 * Летопись Небес (docs/LORE.md): листы, книги, узлы ленты «Нить» и Глоссарий. Структура лежит в `data/celestial/lore/lore.json`
 * (его пишет tools/gen_lore.py из tools/lore_data.py), тексты — переводы `lore.celestial.*`. Открытые листы хранятся
 * в {@link PlayerData#lore()}: id листа или «gloss:&lt;слово&gt;» для Глоссария.
 */
public final class Lore {
	public record Sheet(String id, int book, String node, String art, String src, boolean quote, boolean scripture, boolean apocrypha,
		boolean tradition, List<String> gloss) {}

	public record Node(String id, int act) {}

	private static final String PATH = "/data/celestial/lore/lore.json";
	private static Map<String, Sheet> sheets;
	private static List<Node> nodes;
	private static List<Integer> books;
	private static List<String> glossary;

	private Lore() {}

	private static synchronized void load() {
		if (sheets != null) {
			return;
		}
		Map<String, Sheet> loadedSheets = new LinkedHashMap<>();
		List<Node> loadedNodes = new ArrayList<>();
		List<Integer> loadedBooks = new ArrayList<>();
		List<String> loadedGlossary = new ArrayList<>();
		try (var in = Lore.class.getResourceAsStream(PATH)) {
			if (in == null) {
				throw new IllegalStateException("нет " + PATH);
			}
			JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
			for (JsonElement e : root.getAsJsonArray("books")) {
				loadedBooks.add(e.getAsInt());
			}
			for (JsonElement e : root.getAsJsonArray("nodes")) {
				loadedNodes.add(new Node(e.getAsJsonObject().get("id").getAsString(), e.getAsJsonObject().get("act").getAsInt()));
			}
			for (JsonElement e : root.getAsJsonArray("glossary")) {
				loadedGlossary.add(e.getAsString());
			}
			for (JsonElement e : root.getAsJsonArray("sheets")) {
				JsonObject o = e.getAsJsonObject();
				List<String> gloss = new ArrayList<>();
				for (JsonElement g : (JsonArray) o.get("gloss")) {
					gloss.add(g.getAsString());
				}
				Sheet sheet = new Sheet(o.get("id").getAsString(), o.get("book").getAsInt(), o.get("node").getAsString(), o.get("art").getAsString(),
					o.get("src").getAsString(), o.get("has_quote").getAsBoolean(), o.get("has_s").getAsBoolean(), o.get("has_a").getAsBoolean(),
					o.get("has_t").getAsBoolean(), List.copyOf(gloss));
				loadedSheets.put(sheet.id(), sheet);
			}
		} catch (Exception ex) {
			throw new IllegalStateException("не удалось прочитать Летопись", ex);
		}
		nodes = List.copyOf(loadedNodes);
		books = List.copyOf(loadedBooks);
		glossary = List.copyOf(loadedGlossary);
		sheets = loadedSheets;
	}

	public static List<Sheet> sheets() {
		load();
		return List.copyOf(sheets.values());
	}

	public static Optional<Sheet> sheet(String id) {
		load();
		return Optional.ofNullable(sheets.get(id));
	}

	public static List<Node> nodes() {
		load();
		return nodes;
	}

	public static List<Integer> books() {
		load();
		return books;
	}

	public static List<String> glossary() {
		load();
		return glossary;
	}

	public static List<Sheet> sheetsOfBook(int book) {
		return sheets().stream().filter(s -> s.book() == book).toList();
	}

	public static boolean glossaryKnown(PlayerData d, String id) {
		return d.knowsLore("gloss:" + id);
	}

	/** Сколько листов книги открыто. */
	public static long openInBook(PlayerData d, int book) {
		return sheetsOfBook(book).stream().filter(s -> d.knowsLore(s.id())).count();
	}

	public static long openInNode(PlayerData d, String node) {
		return sheets().stream().filter(s -> s.node().equals(node) && d.knowsLore(s.id())).count();
	}

	public static long totalInNode(String node) {
		return sheets().stream().filter(s -> s.node().equals(node)).count();
	}

	/** Открывает лист (и слова Глоссария, которые он приносит). Возвращает true, если лист был закрыт. Неизвестный id — false. */
	public static boolean unlock(ServerPlayer player, String id) {
		Optional<Sheet> sheet = sheet(id);
		if (sheet.isEmpty()) {
			return false;
		}
		if (CelestialData.get(player).knowsLore(id)) {
			return false;
		}
		CelestialData.update(player, d -> d.withLore(id));
		player.sendOverlayMessage(Component.translatable("lore.celestial.unlocked", Component.translatable("lore.celestial.sheet." + id + ".title")));
		player.level().playSound(null, player.blockPosition(), SoundEvents.BOOK_PAGE_TURN, SoundSource.PLAYERS, 1.0F, 0.9F);
		player.level().playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 0.8F, 1.3F);
		for (String g : sheet.get().gloss()) {
			addGlossary(player, g, false);
		}
		return true;
	}

	/** Слово в Глоссарий (при встрече в игре). */
	public static boolean addGlossary(ServerPlayer player, String id, boolean announce) {
		if (!glossary().contains(id) || CelestialData.get(player).knowsLore("gloss:" + id)) {
			return false;
		}
		CelestialData.update(player, d -> d.withLore("gloss:" + id));
		if (announce) {
			player.sendOverlayMessage(Component.translatable("lore.celestial.glossary_added", Component.translatable("lore.celestial.gloss." + id)));
		}
		return true;
	}

	/** Для тестов и отладки: закрыть лист обратно. */
	public static boolean lock(ServerPlayer player, String id) {
		if (!CelestialData.get(player).knowsLore(id)) {
			return false;
		}
		CelestialData.update(player, d -> d.withoutLore(id));
		return true;
	}
}
