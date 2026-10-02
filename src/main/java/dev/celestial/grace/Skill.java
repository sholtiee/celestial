package dev.celestial.grace;

import java.util.Arrays;
import java.util.List;
import org.jspecify.annotations.Nullable;

/** Навыки Благодати: три ветки — Крылья (полёт), Свет (магия), Твердь (бой). col/row — место в дереве на экране. */
public enum Skill {
	// Крылья
	STAMINA_1("stamina_1", Branch.WINGS, 1, null, 0, 0),
	DOUBLE_JUMP("double_jump", Branch.WINGS, 2, STAMINA_1, 0, 1),
	STAMINA_2("stamina_2", Branch.WINGS, 2, STAMINA_1, 1, 1),
	DASH("dash", Branch.WINGS, 3, DOUBLE_JUMP, 0, 2),
	FEATHER_FALL("feather_fall", Branch.WINGS, 2, DOUBLE_JUMP, 1, 2),
	// Свет
	RADIANCE_POOL("radiance_pool", Branch.LIGHT, 1, null, 0, 0),
	LIGHT_BOLT("light_bolt", Branch.LIGHT, 1, null, 1, 0),
	RADIANCE_REGEN("radiance_regen", Branch.LIGHT, 2, RADIANCE_POOL, 0, 1),
	INNER_LIGHT("inner_light", Branch.LIGHT, 3, RADIANCE_POOL, 0, 2),
	HEALING_LIGHT("healing_light", Branch.LIGHT, 2, LIGHT_BOLT, 1, 1),
	BEACON_RECALL("beacon_recall", Branch.LIGHT, 2, RADIANCE_POOL, 0, 2),
	LIGHT_SHIELD("light_shield", Branch.LIGHT, 3, HEALING_LIGHT, 1, 2),
	STARFALL("starfall", Branch.LIGHT, 4, LIGHT_SHIELD, 1, 3),
	// Твердь
	VIGOR("vigor", Branch.MIGHT, 2, null, 0, 0),
	HEAVENLY_STRIKE("heavenly_strike", Branch.MIGHT, 2, VIGOR, 0, 1),
	RESILIENCE("resilience", Branch.MIGHT, 2, VIGOR, 1, 1),
	FLASH("flash", Branch.MIGHT, 3, HEAVENLY_STRIKE, 0, 2),
	SECOND_WIND("second_wind", Branch.MIGHT, 5, RESILIENCE, 1, 2);

	public enum Branch { WINGS, LIGHT, MIGHT }

	public final String id;
	public final Branch branch;
	public final int cost;
	public final @Nullable Skill requires;
	public final int col;
	public final int row;

	Skill(String id, Branch branch, int cost, @Nullable Skill requires, int col, int row) {
		this.id = id;
		this.branch = branch;
		this.cost = cost;
		this.requires = requires;
		this.col = col;
		this.row = row;
	}

	public static @Nullable Skill byId(String id) {
		return Arrays.stream(values()).filter(s -> s.id.equals(id)).findFirst().orElse(null);
	}

	public static List<Skill> branch(Branch branch) {
		return Arrays.stream(values()).filter(s -> s.branch == branch).toList();
	}
}
