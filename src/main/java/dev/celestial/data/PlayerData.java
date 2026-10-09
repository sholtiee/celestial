package dev.celestial.data;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;

/**
 * Прогресс игрока в Саге Небес. Неизменяемый: любые правки возвращают новую копию
 * (так Fabric-вложение само замечает изменение и синхронизирует его с клиентом).
 */
public record PlayerData(int grace, List<String> skills, int reputation, List<String> codex, List<String> trials, float radiance,
	List<String> quests, float fear, float warmth, List<String> lore) {
	public static final float MAX_RADIANCE = 100.0F;
	public static final float MAX_FEAR = 100.0F;
	public static final PlayerData EMPTY = new PlayerData(0, List.of(), 0, List.of(), List.of(), MAX_RADIANCE, List.of(), 0.0F, 100.0F, List.of());

	public static final Codec<PlayerData> CODEC = RecordCodecBuilder.create(i -> i.group(
		Codec.INT.optionalFieldOf("grace", 0).forGetter(PlayerData::grace),
		Codec.STRING.listOf().optionalFieldOf("skills", List.of()).forGetter(PlayerData::skills),
		Codec.INT.optionalFieldOf("reputation", 0).forGetter(PlayerData::reputation),
		Codec.STRING.listOf().optionalFieldOf("codex", List.of()).forGetter(PlayerData::codex),
		Codec.STRING.listOf().optionalFieldOf("trials", List.of()).forGetter(PlayerData::trials),
		Codec.FLOAT.optionalFieldOf("radiance", MAX_RADIANCE).forGetter(PlayerData::radiance),
		Codec.STRING.listOf().optionalFieldOf("quests", List.of()).forGetter(PlayerData::quests),
		Codec.FLOAT.optionalFieldOf("fear", 0.0F).forGetter(PlayerData::fear),
		Codec.FLOAT.optionalFieldOf("warmth", 100.0F).forGetter(PlayerData::warmth),
		Codec.STRING.listOf().optionalFieldOf("lore", List.of()).forGetter(PlayerData::lore)
	).apply(i, PlayerData::new));
	public static final StreamCodec<RegistryFriendlyByteBuf, PlayerData> STREAM_CODEC = ByteBufCodecs.fromCodecWithRegistries(CODEC);

	public boolean hasSkill(String id) {
		return skills.contains(id);
	}

	public boolean knows(String codexEntry) {
		return codex.contains(codexEntry);
	}

	public boolean passed(String trial) {
		return trials.contains(trial);
	}

	public PlayerData withGrace(int value) {
		return new PlayerData(Math.max(0, value), skills, reputation, codex, trials, radiance, quests, fear, warmth, lore);
	}

	public PlayerData withSkill(String id) {
		return hasSkill(id) ? this : new PlayerData(grace, append(skills, id), reputation, codex, trials, radiance, quests, fear, warmth, lore);
	}

	/** Для тестов: забыть все навыки. */
	public PlayerData withoutSkills() {
		return new PlayerData(grace, List.of(), reputation, codex, trials, radiance, quests, fear, warmth, lore);
	}

	public PlayerData withReputation(int value) {
		return new PlayerData(grace, skills, value, codex, trials, radiance, quests, fear, warmth, lore);
	}

	/** Для тестов и администраторов: убрать запись Кодекса (например, «memory:fruit» — чтобы Отблеск снова был «первым»). */
	public PlayerData withoutCodex(String entry) {
		return !knows(entry) ? this : new PlayerData(grace, skills, reputation, codex.stream().filter(e -> !e.equals(entry)).toList(), trials, radiance,
			quests, fear, warmth, lore);
	}

	public PlayerData withCodex(String entry) {
		return knows(entry) ? this : new PlayerData(grace, skills, reputation, append(codex, entry), trials, radiance, quests, fear, warmth, lore);
	}

	public PlayerData withTrial(String trial) {
		return passed(trial) ? this : new PlayerData(grace, skills, reputation, codex, append(trials, trial), radiance, quests, fear, warmth, lore);
	}

	public PlayerData withRadiance(float value) {
		return new PlayerData(grace, skills, reputation, codex, trials, Math.max(0, value), quests, fear, warmth, lore);
	}

	public PlayerData withQuests(List<String> value) {
		return new PlayerData(grace, skills, reputation, codex, trials, radiance, List.copyOf(value), fear, warmth, lore);
	}

	/** Страх тьмы в Бездне (0–100). */
	public PlayerData withFear(float value) {
		return new PlayerData(grace, skills, reputation, codex, trials, radiance, quests, Math.max(0, Math.min(MAX_FEAR, value)), warmth, lore);
	}

	/** Тепло в Ледяных Чертогах (0–100). */
	public PlayerData withWarmth(float value) {
		return new PlayerData(grace, skills, reputation, codex, trials, radiance, quests, fear, Math.max(0, Math.min(100, value)), lore);
	}

	/** Открытые листы Летописи (id листа) и слова Глоссария («gloss:<id>»). */
	public boolean knowsLore(String id) {
		return lore.contains(id);
	}

	public PlayerData withLore(String id) {
		return knowsLore(id) ? this : new PlayerData(grace, skills, reputation, codex, trials, radiance, quests, fear, warmth, append(lore, id));
	}

	public PlayerData withoutLore(String id) {
		if (!knowsLore(id)) {
			return this;
		}
		List<String> copy = new ArrayList<>(lore);
		copy.remove(id);
		return new PlayerData(grace, skills, reputation, codex, trials, radiance, quests, fear, warmth, List.copyOf(copy));
	}

	private static List<String> append(List<String> list, String value) {
		List<String> copy = new ArrayList<>(list);
		copy.add(value);
		return List.copyOf(copy);
	}
}
