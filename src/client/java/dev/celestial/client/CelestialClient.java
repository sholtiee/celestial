package dev.celestial.client;

import dev.celestial.client.dev.AutoPilot;
import dev.celestial.client.render.CelestialRenderers;
import net.fabricmc.api.ClientModInitializer;

public class CelestialClient implements ClientModInitializer {
	@Override
	public void onInitializeClient() {
		ClientState.init();
		CameraShake.init();
		dev.celestial.client.grace.LorePanel.initNetwork();
		// трава Рая окрашивается цветом травы биома (золото на лугах, серый на Грозовом пике и т. д.)
		net.fabricmc.fabric.api.client.rendering.v1.BlockColorRegistry.register(
			java.util.List.of(heavenTint(net.minecraft.client.color.block.BlockTintSources.grassBlock())), dev.celestial.registry.ModBlocks.GOLDEN_GRASS);
		net.fabricmc.fabric.api.client.rendering.v1.BlockColorRegistry.register(
			java.util.List.of(heavenTint(net.minecraft.client.color.block.BlockTintSources.grass())), dev.celestial.registry.ModBlocks.GOLDEN_TUFT);
		net.fabricmc.fabric.api.client.rendering.v1.BlockColorRegistry.register(
			java.util.List.of(heavenTint(net.minecraft.client.color.block.BlockTintSources.doubleTallGrass())), dev.celestial.registry.ModBlocks.TALL_GOLDEN_GRASS);
		CelestialRenderers.init();
		SeraphWingsController.init();
		dev.celestial.client.grace.GraceClient.init();
		AutoPilot.init();
	}

	private static final int GOLD = 0xFFF0C94A;

	/** В Раю трава красится цветом биома (золото/серый), в других измерениях — всегда золотая, а не зелёная от биома Верхнего мира. */
	private static net.minecraft.client.color.block.BlockTintSource heavenTint(net.minecraft.client.color.block.BlockTintSource delegate) {
		return new net.minecraft.client.color.block.BlockTintSource() {
			@Override
			public int color(net.minecraft.world.level.block.state.BlockState state) {
				return delegate.color(state);
			}

			@Override
			public int colorInWorld(net.minecraft.world.level.block.state.BlockState state, net.minecraft.client.renderer.block.BlockAndTintGetter level,
				net.minecraft.core.BlockPos pos) {
				var mc = net.minecraft.client.Minecraft.getInstance();
				boolean heaven = mc.level != null && mc.level.dimension() == dev.celestial.world.HeavenDimension.HEAVEN;
				return heaven ? delegate.colorInWorld(state, level, pos) : GOLD;
			}

			@Override
			public java.util.Set<net.minecraft.world.level.block.state.properties.Property<?>> relevantProperties() {
				return delegate.relevantProperties();
			}
		};
	}
}
