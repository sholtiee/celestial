package dev.celestial.item;

import java.util.List;
import net.minecraft.world.item.Item;

/** Руна для Алтаря наделения: список небесных зачарований, которые она может дать (первое подходящее к предмету). */
public class RuneItem extends Item {
	private final List<String> enchantments;

	public RuneItem(List<String> enchantments, Properties properties) {
		super(properties);
		this.enchantments = enchantments;
	}

	public List<String> enchantments() {
		return enchantments;
	}
}
