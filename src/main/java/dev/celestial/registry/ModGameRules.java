package dev.celestial.registry;

import dev.celestial.Celestial;
import net.fabricmc.fabric.api.gamerule.v1.GameRuleBuilder;
import net.minecraft.world.level.gamerules.GameRule;
import net.minecraft.world.level.gamerules.GameRuleCategory;

/** Правила игры Celestial: /gamerule celestial:fading false — полностью отключает влияние на Верхний мир. */
public final class ModGameRules {
	public static final GameRule<Boolean> FADING = GameRuleBuilder.forBoolean(true)
		.category(GameRuleCategory.MISC).buildAndRegister(Celestial.id("fading"));
	public static final GameRule<Boolean> METEORS = GameRuleBuilder.forBoolean(true)
		.category(GameRuleCategory.MISC).buildAndRegister(Celestial.id("meteors"));
	/** Через сколько игровых дней Угасание усиливается на одну стадию. */
	public static final GameRule<Integer> FADING_DAYS = GameRuleBuilder.forInteger(10).range(1, 1000)
		.category(GameRuleCategory.MISC).buildAndRegister(Celestial.id("fading_days"));

	/** Пролог «Сон о Начале» при первом входе в мир (docs/LORE.md §5a). Для серверов, где он не нужен: /gamerule celestial:prologue false. */
	public static final GameRule<Boolean> PROLOGUE = GameRuleBuilder.forBoolean(true)
		.category(GameRuleCategory.MISC).buildAndRegister(Celestial.id("prologue"));

	private ModGameRules() {}

	public static void init() {
	}
}
