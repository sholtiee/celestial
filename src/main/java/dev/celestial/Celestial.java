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
		dev.celestial.registry.ModGameRules.init();
		dev.celestial.registry.ModSounds.init();
		dev.celestial.data.CelestialData.init();
		dev.celestial.network.CelestialNetwork.init();
		dev.celestial.command.CelestialCommand.init();
		dev.celestial.registry.ModFeatures.init();
		ModBlocks.init();
		ModItems.init();
		ModEntities.init();
		dev.celestial.registry.ModEffects.init();
		dev.celestial.registry.ModBlockEntities.init();
		ModCreativeTab.init();
		dev.celestial.world.dim.DimensionPhysics.init();
		dev.celestial.item.EquipmentEffects.init();
		dev.celestial.story.StoryEvents.init();
		dev.celestial.quest.Quests.init();
		dev.celestial.grace.Grace.init();
		dev.celestial.grace.CodexEvents.init();
		dev.celestial.fading.Fading.init();
		dev.celestial.fading.Stargazer.init();
		dev.celestial.world.abyss.Darkness.init();
		dev.celestial.world.CaveFloorStructure.init();
		LOGGER.info("Celestial: небеса открываются");
	}

	public static Identifier id(String path) {
		return Identifier.fromNamespaceAndPath(MOD_ID, path);
	}
}
