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
		dev.celestial.registry.ModParticles.init();
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
		dev.celestial.puzzle.Attempts.init();
		dev.celestial.trial.TrialGuard.init();
		// статические карты со временем/позициями не должны жить между мирами одиночной игры
		net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents.SERVER_STOPPED.register(server -> {
			dev.celestial.grace.Grace.clearState();
			dev.celestial.block.light.LightReceiverBlock.clearState();
			dev.celestial.block.machine.CloudLiftBlock.clearState();
			dev.celestial.block.machine.BeamPowered.LAST_BEAM.clear();
			dev.celestial.starlight.Wards.clear();
		});
		dev.celestial.world.frozen.Cold.init();
		dev.celestial.world.CaveFloorStructure.init();
		LOGGER.info("Celestial: небеса открываются");
	}

	public static Identifier id(String path) {
		return Identifier.fromNamespaceAndPath(MOD_ID, path);
	}
}
