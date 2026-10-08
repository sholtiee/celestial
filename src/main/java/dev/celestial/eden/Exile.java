package dev.celestial.eden;

import dev.celestial.registry.ModEffects;
import net.minecraft.world.entity.player.Player;

/** «Изгнание» (LORE §7): кто вкусил плод Познания, 10 минут не допускается к Древу Жизни, а ангелы с ним холодны. Лист смоковницы снимает его. */
public final class Exile {
	public static final int DURATION = 12000;

	private Exile() {}

	public static boolean isExiled(Player player) {
		return player.hasEffect(ModEffects.EXILE);
	}
}
