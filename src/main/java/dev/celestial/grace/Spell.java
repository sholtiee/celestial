package dev.celestial.grace;

import org.jspecify.annotations.Nullable;

/** Заклинания Сияния. requires — навык, открывающий заклинание (null — доступно сразу). */
public enum Spell {
	SCOUTS("scouts", 20, null),
	LIGHT_BOLT("light_bolt", 15, Skill.LIGHT_BOLT),
	HEALING_LIGHT("healing_light", 30, Skill.HEALING_LIGHT),
	LIGHT_SHIELD("light_shield", 40, Skill.LIGHT_SHIELD),
	BEACON_RECALL("beacon_recall", 50, Skill.BEACON_RECALL),
	STARFALL("starfall", 60, Skill.STARFALL),
	FLASH("flash", 35, Skill.FLASH);

	public final String id;
	public final int cost;
	public final @Nullable Skill requires;

	Spell(String id, int cost, @Nullable Skill requires) {
		this.id = id;
		this.cost = cost;
		this.requires = requires;
	}
}
