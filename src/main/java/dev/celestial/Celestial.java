package dev.celestial;

import dev.celestial.registry.ModBlocks;
import dev.celestial.registry.ModCreativeTab;
import dev.celestial.registry.ModEntities;
import dev.celestial.registry.ModItems;
import dev.celestial.world.HeavenDimension;
import net.fabricmc.api.ModInitializer;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Celestial implements ModInitializer {
	public static final String MOD_ID = "celestial";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	@Override
	public void onInitialize() {
		ModBlocks.init();
		ModItems.init();
		ModEntities.init();
		ModCreativeTab.init();
		HeavenDimension.init();
		dev.celestial.item.EquipmentEffects.init();
		LOGGER.info("Celestial: небеса открываются");
	}

	public static Identifier id(String path) {
		return Identifier.fromNamespaceAndPath(MOD_ID, path);
	}
}
