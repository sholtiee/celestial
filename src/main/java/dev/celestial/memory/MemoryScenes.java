package dev.celestial.memory;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import dev.celestial.Celestial;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import net.minecraft.world.phys.Vec3;

/**
 * Сцены воспоминаний — данные из `data/celestial/memory/scenes.json` (генерирует `tools/gen_scenes.py`; руками не править).
 * Сцена: шаблон сцены (`stage`), центр и радиус памяти, точка появления странника, лист Летописи, мысль по возвращении, актёры и шаги.
 * Координаты — относительно угла шаблона.
 */
public final class MemoryScenes {
	private static final String PATH = "/data/celestial/memory/scenes.json";
	private static Map<String, Scene> scenes;

	public record Actor(String id, String type, String skin, Vec3 pos, float yaw, int pose) {}

	public record Scene(String id, String stage, Vec3 center, double radius, Vec3 spawn, float spawnYaw, String sheet, String thought,
		String onComplete, List<Actor> actors, List<JsonObject> steps) {}

	private MemoryScenes() {}

	public static Optional<Scene> get(String id) {
		if (scenes == null) {
			load();
		}
		return Optional.ofNullable(scenes.get(id));
	}

	/** Сцена, которая открывает этот лист Летописи (для кнопки «Пережить снова»). */
	public static Optional<Scene> forSheet(String sheet) {
		if (scenes == null) {
			load();
		}
		return scenes.values().stream().filter(s -> s.sheet().equals(sheet)).findFirst();
	}

	public static List<String> ids() {
		if (scenes == null) {
			load();
		}
		return List.copyOf(scenes.keySet());
	}

	static Vec3 vec(JsonElement e) {
		JsonArray a = e.getAsJsonArray();
		return new Vec3(a.get(0).getAsDouble(), a.get(1).getAsDouble(), a.get(2).getAsDouble());
	}

	private static synchronized void load() {
		Map<String, Scene> map = new HashMap<>();
		try (var in = MemoryScenes.class.getResourceAsStream(PATH)) {
			if (in != null) {
				JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
				for (var entry : root.entrySet()) {
					JsonObject o = entry.getValue().getAsJsonObject();
					List<Actor> actors = new ArrayList<>();
					for (JsonElement a : o.getAsJsonArray("actors")) {
						JsonObject ao = a.getAsJsonObject();
						actors.add(new Actor(ao.get("id").getAsString(), ao.get("type").getAsString(), ao.get("skin").getAsString(),
							vec(ao.get("pos")), ao.has("yaw") ? ao.get("yaw").getAsFloat() : 0.0F, ao.has("pose") ? ao.get("pose").getAsInt() : 0));
					}
					List<JsonObject> steps = new ArrayList<>();
					for (JsonElement s : o.getAsJsonArray("steps")) {
						steps.add(s.getAsJsonObject());
					}
					JsonArray spawn = o.getAsJsonArray("spawn");
					map.put(entry.getKey(), new Scene(entry.getKey(), o.get("stage").getAsString(), vec(o.get("center")), o.get("radius").getAsDouble(),
						new Vec3(spawn.get(0).getAsDouble(), spawn.get(1).getAsDouble(), spawn.get(2).getAsDouble()), spawn.get(3).getAsFloat(),
						o.get("sheet").getAsString(), o.get("thought").getAsString(), o.has("on_complete") ? o.get("on_complete").getAsString() : "",
						List.copyOf(actors), List.copyOf(steps)));
				}
			}
		} catch (Exception e) {
			Celestial.LOGGER.error("Не удалось прочитать сцены воспоминаний {}", PATH, e);
		}
		scenes = map;
	}
}
