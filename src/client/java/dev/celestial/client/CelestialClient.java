package dev.celestial.client;

import dev.celestial.client.dev.AutoPilot;
import dev.celestial.client.render.CelestialRenderers;
import net.fabricmc.api.ClientModInitializer;

public class CelestialClient implements ClientModInitializer {
	@Override
	public void onInitializeClient() {
		ClientState.init();
		// трава Рая окрашивается цветом травы биома (золото на лугах, серый на Грозовом пике и т. д.)
		net.fabricmc.fabric.api.client.rendering.v1.BlockColorRegistry.register(
			java.util.List.of(net.minecraft.client.color.block.BlockTintSources.grassBlock()), dev.celestial.registry.ModBlocks.GOLDEN_GRASS);
		net.fabricmc.fabric.api.client.rendering.v1.BlockColorRegistry.register(
			java.util.List.of(net.minecraft.client.color.block.BlockTintSources.grass()), dev.celestial.registry.ModBlocks.GOLDEN_TUFT);
		net.fabricmc.fabric.api.client.rendering.v1.BlockColorRegistry.register(
			java.util.List.of(net.minecraft.client.color.block.BlockTintSources.doubleTallGrass()), dev.celestial.registry.ModBlocks.TALL_GOLDEN_GRASS);
		CelestialRenderers.init();
		SeraphWingsController.init();
		dev.celestial.client.grace.GraceClient.init();
		AutoPilot.init();
	}
}
