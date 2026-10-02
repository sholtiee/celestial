package dev.celestial.data;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.ArrayList;
import java.util.List;

/** Общее состояние мира: стадия Угасания (0–5), пройденный акт саги, сюжетные флаги. Хранится на Верхнем мире. */
public record WorldState(int fading, int act, List<String> flags, long lastFadingDay) {
	public static final int MAX_FADING = 5;
	public static final WorldState INITIAL = new WorldState(1, 0, List.of(), 0L);

	public static final Codec<WorldState> CODEC = RecordCodecBuilder.create(i -> i.group(
		Codec.INT.optionalFieldOf("fading", 1).forGetter(WorldState::fading),
		Codec.INT.optionalFieldOf("act", 0).forGetter(WorldState::act),
		Codec.STRING.listOf().optionalFieldOf("flags", List.of()).forGetter(WorldState::flags),
		Codec.LONG.optionalFieldOf("last_fading_day", 0L).forGetter(WorldState::lastFadingDay)
	).apply(i, WorldState::new));

	public boolean has(String flag) {
		return flags.contains(flag);
	}

	public WorldState withFading(int value) {
		return new WorldState(Math.max(0, Math.min(MAX_FADING, value)), act, flags, lastFadingDay);
	}

	public WorldState withAct(int value) {
		return new WorldState(fading, Math.max(act, value), flags, lastFadingDay);
	}

	public WorldState withFlag(String flag) {
		if (has(flag)) {
			return this;
		}
		List<String> copy = new ArrayList<>(flags);
		copy.add(flag);
		return new WorldState(fading, act, List.copyOf(copy), lastFadingDay);
	}

	public WorldState withLastFadingDay(long day) {
		return new WorldState(fading, act, flags, day);
	}
}
