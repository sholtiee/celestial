package dev.celestial.story;

import dev.celestial.Celestial;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;

/** Главы сюжета «Угасающий свет» — это ветка достижений celestial:story/*. */
public enum Story {
	ROOT("root"),
	FLAME("flame_of_the_deep"),
	VOID("heart_of_the_void"),
	GATES("gates_of_heaven"),
	SERAPH("fall_of_the_seraph"),
	FINALE("light_returns"),
	ABYSS("beneath_the_clouds"),
	DEVOURER("heart_of_darkness"),
	FROZEN("frozen_wings"),
	ARCHON("crown_of_frost"),
	CLOCKWORK("clockwork"),
	CLOCKMAKER("gear_of_eternity"),
	ASTRAL("star_path"),
	KINDLED("light_kindled"),
	CONSUMED("light_consumed"),
	NAMED("true_name"),
	GLACIER_MASTER("glacier_master"),
	CLOCK_DIALS("clock_dials"),
	TICK_WALKER("tick_walker"),
	REWIND_ROOM("rewind_room"),
	BABEL_TONGUES("babel_tongues"),
	THREE_BEAMS("three_beams"),
	BELL_RINGER("bell_ringer"),
	STAR_WALKER("star_walker"),
	RIDDLE("riddle_solved"),
	STAR_LOCK("star_lock"),
	MEMORY("memory_keeper"),
	ECHO("echo_listener"),
	PUZZLE_MASTER("puzzle_master"),
	TRIAL_CHAMPION("trial_champion"),
	SERAPH_FLAWLESS("seraph_flawless"),
	SERAPH_SWIFT("seraph_swift"),
	DEVOURER_FLAWLESS("devourer_flawless"),
	DEVOURER_SWIFT("devourer_swift"),
	ARCHON_FLAWLESS("archon_flawless"),
	ARCHON_SWIFT("archon_swift"),
	CLOCKMAKER_FLAWLESS("clockmaker_flawless"),
	CLOCKMAKER_SWIFT("clockmaker_swift"),
	FACELESS_FLAWLESS("faceless_flawless"),
	FACELESS_SWIFT("faceless_swift");

	/** Вид загадки (как в PuzzleRewards.solved) → достижение; все восемь вместе дают «Мастера загадок». */
	public static final java.util.Map<String, Story> PUZZLES = java.util.Map.ofEntries(
		java.util.Map.entry("bells", BELL_RINGER), java.util.Map.entry("star_tiles", STAR_WALKER), java.util.Map.entry("riddle", RIDDLE),
		java.util.Map.entry("star_lock", STAR_LOCK), java.util.Map.entry("memory", MEMORY), java.util.Map.entry("echo", ECHO),
		java.util.Map.entry("glacier", GLACIER_MASTER), java.util.Map.entry("mirror_maze", THREE_BEAMS),
		java.util.Map.entry("clock_dials", CLOCK_DIALS), java.util.Map.entry("tick_platforms", TICK_WALKER), java.util.Map.entry("rewind_room", REWIND_ROOM),
		java.util.Map.entry("babel", BABEL_TONGUES));

	public final Identifier id;

	Story(String path) {
		this.id = Celestial.id("story/" + path);
	}

	public boolean isDone(ServerPlayer player) {
		AdvancementHolder holder = player.level().getServer().getAdvancements().get(id);
		return holder != null && player.getAdvancements().getOrStartProgress(holder).isDone();
	}

	/** Выдаёт главу программно (для финала — у него критерий «impossible»). */
	public void grant(ServerPlayer player) {
		AdvancementHolder holder = player.level().getServer().getAdvancements().get(id);
		if (holder == null) {
			return;
		}
		for (String criterion : player.getAdvancements().getOrStartProgress(holder).getRemainingCriteria()) {
			player.getAdvancements().award(holder, criterion);
		}
	}
}
