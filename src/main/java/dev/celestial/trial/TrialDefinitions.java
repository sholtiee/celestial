package dev.celestial.trial;

import dev.celestial.registry.ModEntities;
import dev.celestial.trial.TrialDefinition.Spawn;
import dev.celestial.trial.TrialDefinition.Type;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Испытания Башни Рая (7 этажей). Новые башни других измерений добавляются сюда же. */
final class TrialDefinitions {
	private TrialDefinitions() {}

	static Map<String, TrialDefinition> build() {
		Map<String, TrialDefinition> map = new HashMap<>();
		put(map, new TrialDefinition("heaven_1", Type.WAVES, 0, List.of(
			List.of(new Spawn(() -> ModEntities.FALLEN_GUARDIAN, 3)),
			List.of(new Spawn(() -> ModEntities.FALLEN_GUARDIAN, 2), new Spawn(() -> ModEntities.STORM_SPIRIT, 1))), 1));
		put(map, new TrialDefinition("heaven_2", Type.PARKOUR, 60, List.of(), 1));
		put(map, new TrialDefinition("heaven_3", Type.PUZZLE, 0, List.of(), 1));
		put(map, new TrialDefinition("heaven_4", Type.PUZZLE, 0, List.of(), 1));
		put(map, new TrialDefinition("heaven_5", Type.PARKOUR, 90, List.of(), 2));
		put(map, new TrialDefinition("heaven_6", Type.BARE_WAVES, 0, List.of(
			List.of(new Spawn(() -> ModEntities.WINGED_SERPENT, 2)),
			List.of(new Spawn(() -> ModEntities.FALLEN_GUARDIAN, 2), new Spawn(() -> ModEntities.WINGED_SERPENT, 1))), 2));
		put(map, new TrialDefinition("heaven_7", Type.WAVES, 0, List.of(
			List.of(new Spawn(() -> ModEntities.STORM_SPIRIT, 3)),
			List.of(new Spawn(() -> ModEntities.FALLEN_GUARDIAN, 3), new Spawn(() -> ModEntities.MIMIC, 1)),
			List.of(new Spawn(() -> ModEntities.STORM_ELEMENTAL, 1))), 3));
		put(map, new TrialDefinition("cloud_castle", Type.WAVES, 0, List.of(
			List.of(new Spawn(() -> ModEntities.STORM_SPIRIT, 2), new Spawn(() -> ModEntities.WINGED_SERPENT, 2)),
			List.of(new Spawn(() -> ModEntities.STORM_ELEMENTAL, 1), new Spawn(() -> ModEntities.STORM_SPIRIT, 2))), 3));
		// Ванильные измерения (Угасание): Пылающее святилище (Ад) и Разлом Пустоты (Энд)
		put(map, new TrialDefinition("flame_sanctuary", Type.WAVES, 0, List.of(
			List.of(new Spawn(() -> net.minecraft.world.entity.EntityTypes.BLAZE, 2), new Spawn(() -> net.minecraft.world.entity.EntityTypes.WITHER_SKELETON, 2)),
			List.of(new Spawn(() -> net.minecraft.world.entity.EntityTypes.MAGMA_CUBE, 3), new Spawn(() -> net.minecraft.world.entity.EntityTypes.BLAZE, 2)),
			List.of(new Spawn(() -> net.minecraft.world.entity.EntityTypes.WITHER_SKELETON, 3), new Spawn(() -> net.minecraft.world.entity.EntityTypes.BLAZE, 3))), 3));
		put(map, new TrialDefinition("void_rift", Type.WAVES, 0, List.of(
			List.of(new Spawn(() -> net.minecraft.world.entity.EntityTypes.ENDERMAN, 3)),
			List.of(new Spawn(() -> ModEntities.SHADOW, 3), new Spawn(() -> net.minecraft.world.entity.EntityTypes.ENDERMITE, 4)),
			List.of(new Spawn(() -> ModEntities.SHADOW, 2), new Spawn(() -> net.minecraft.world.entity.EntityTypes.ENDERMAN, 3))), 3));
		return map;
	}

	private static void put(Map<String, TrialDefinition> map, TrialDefinition def) {
		map.put(def.id(), def);
	}
}
