package dev.celestial.puzzle;

import dev.celestial.registry.ModItems;
import java.util.List;
import java.util.function.Supplier;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;

/** Загадки рунных пьедесталов: текст — в переводах (puzzle.celestial.riddle.N), ответ — предмет. */
public final class Riddles {
	private static final List<Supplier<Item>> ANSWERS = List.of(
		() -> Items.FEATHER,            // «Падаю, но не разбиваюсь; лечу, но крыльев у меня нет…»
		() -> ModItems.CLOUD_FLUFF,     // «Мягче пуха, белее снега, держит тех, кто ходит по небу»
		() -> Items.CLOCK,              // «Без ног иду, без рук указываю…»
		() -> Items.GLOWSTONE_DUST,     // «Рождён во тьме Ада, но несу свет»
		() -> ModItems.MANNA_BERRIES,   // «Пища, что падает с неба…»
		() -> Items.COMPASS,            // «Всегда смотрю в одну сторону…»
		() -> Items.ECHO_SHARD,         // «Скажи моё имя — и меня не станет» (тишина → эхо)
		() -> ModItems.STARQUARTZ       // «Упала с неба, но не дождь; светит, но не огонь»
	);
	public static final int COUNT = 8;

	private Riddles() {}

	public static Item answer(int index) {
		return ANSWERS.get(Math.floorMod(index, ANSWERS.size())).get();
	}
}
