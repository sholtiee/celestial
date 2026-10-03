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
	DEVOURER("heart_of_darkness");

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
