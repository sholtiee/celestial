package dev.celestial.trial;

import java.util.List;
import java.util.Map;
import java.util.function.Supplier;
import net.minecraft.world.entity.EntityType;

/**
 * Описание испытания. Тип определяет условие победы:
 * WAVES — перебить все волны; PARKOUR — добежать до Финишного кристалла за время;
 * PUZZLE — решить загадку рядом (приёмник, колокола, плитки, пьедестал дают сигнал); BARE_WAVES — волны без брони.
 */
public record TrialDefinition(String id, Type type, int timeLimitSeconds, List<List<Spawn>> waves, int grace) {
	public enum Type { WAVES, PARKOUR, PUZZLE, BARE_WAVES }

	public record Spawn(Supplier<EntityType<?>> type, int count) {}

	private static Map<String, TrialDefinition> registry;

	public static TrialDefinition get(String id) {
		if (registry == null) {
			registry = TrialDefinitions.build();
		}
		return registry.get(id);
	}
}
