package dev.celestial.quest;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;

/**
 * Поручение ангелов. Хранится в PlayerData строкой «тип;цель;нужно;сделано;награда;кол-во;репутация».
 * KILL — убить мобов, BRING — принести предметы на доску, EXPLORE — побывать в постройке.
 */
public record Quest(Type type, String target, int need, int progress, String reward, int rewardCount, int reputation) {
	public enum Type { KILL, BRING, EXPLORE }

	public static Quest decode(String s) {
		String[] p = s.split(";");
		return new Quest(Type.valueOf(p[0]), p[1], Integer.parseInt(p[2]), Integer.parseInt(p[3]), p[4], Integer.parseInt(p[5]), Integer.parseInt(p[6]));
	}

	public String encode() {
		return String.join(";", type.name(), target, String.valueOf(need), String.valueOf(progress), reward, String.valueOf(rewardCount),
			String.valueOf(reputation));
	}

	public Quest withProgress(int value) {
		return new Quest(type, target, need, Math.min(need, value), reward, rewardCount, reputation);
	}

	public boolean isComplete() {
		return progress >= need;
	}

	/** Совпадение по типу и цели (одно и то же поручение дважды не берётся). */
	public boolean sameAs(Quest other) {
		return type == other.type && target.equals(other.target);
	}

	public Component describe() {
		Identifier id = Identifier.parse(target);
		Component what = switch (type) {
			case KILL -> BuiltInRegistries.ENTITY_TYPE.getValue(id).getDescription();
			case BRING -> BuiltInRegistries.ITEM.getValue(id).getName(BuiltInRegistries.ITEM.getValue(id).getDefaultInstance());
			case EXPLORE -> Component.translatable("structure." + id.getNamespace() + "." + id.getPath());
		};
		return Component.translatable("quest.celestial." + type.name().toLowerCase(), what, need, progress);
	}

	public Component describeReward() {
		return Component.translatable("quest.celestial.reward", rewardCount, BuiltInRegistries.ITEM.getValue(Identifier.parse(reward)).getDefaultInstance().getHoverName(), reputation);
	}
}
