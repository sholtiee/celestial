package dev.celestial.chrono;

import dev.celestial.registry.ModItems;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;

/** Хронитовый комплект: в полном — откат реликвий времени (Песочные часы, Шестерня Вечности) короче на четверть. */
public final class ChronoGear {
	private ChronoGear() {}

	public static boolean fullSet(Player p) {
		return p.getItemBySlot(EquipmentSlot.HEAD).is(ModItems.CHRONITE_HELMET) && p.getItemBySlot(EquipmentSlot.CHEST).is(ModItems.CHRONITE_CHESTPLATE)
			&& p.getItemBySlot(EquipmentSlot.LEGS).is(ModItems.CHRONITE_LEGGINGS) && p.getItemBySlot(EquipmentSlot.FEET).is(ModItems.CHRONITE_BOOTS);
	}

	public static int cooldown(Player p, int base) {
		return fullSet(p) ? base * 3 / 4 : base;
	}
}
