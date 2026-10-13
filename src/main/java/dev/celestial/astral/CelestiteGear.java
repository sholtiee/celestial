package dev.celestial.astral;

import dev.celestial.registry.ModItems;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;

/** Целеститовый комплект: в полном — Сияние восстанавливается в полтора раза быстрее, Тьма не держится (свет внутри). */
public final class CelestiteGear {
	private CelestiteGear() {}

	public static boolean fullSet(Player p) {
		return p.getItemBySlot(EquipmentSlot.HEAD).is(ModItems.CELESTITE_HELMET) && p.getItemBySlot(EquipmentSlot.CHEST).is(ModItems.CELESTITE_CHESTPLATE)
			&& p.getItemBySlot(EquipmentSlot.LEGS).is(ModItems.CELESTITE_LEGGINGS) && p.getItemBySlot(EquipmentSlot.FEET).is(ModItems.CELESTITE_BOOTS);
	}
}
