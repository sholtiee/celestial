package dev.celestial.client.render;

import dev.celestial.Celestial;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.LayerDefinition;

public final class ModModelLayers {
	public static final ModelLayerLocation HUMANOID = layer("humanoid");
	public static final ModelLayerLocation PEGASUS = layer("pegasus");
	public static final ModelLayerLocation CLOUD_WHALE = layer("cloud_whale");
	public static final ModelLayerLocation LIGHT_WISP = layer("light_wisp");

	private ModModelLayers() {}

	private static ModelLayerLocation layer(String name) {
		return new ModelLayerLocation(Celestial.id(name), "main");
	}

	public static void init() {
		ModelLayerRegistry.registerModelLayer(HUMANOID, () -> LayerDefinition.create(HumanoidModel.createMesh(CubeDeformation.NONE, 0.0F), 64, 64));
		ModelLayerRegistry.registerModelLayer(PEGASUS, PegasusModel::createBodyLayer);
		ModelLayerRegistry.registerModelLayer(CLOUD_WHALE, CloudWhaleModel::createBodyLayer);
		ModelLayerRegistry.registerModelLayer(LIGHT_WISP, LightWispModel::createBodyLayer);
	}
}
