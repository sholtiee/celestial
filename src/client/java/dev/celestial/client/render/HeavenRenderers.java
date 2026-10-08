package dev.celestial.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.celestial.Celestial;
import dev.celestial.registry.ModEntities;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Mob;

/** Рендеры существ со своими моделями из {@link HeavenModels} + светящийся слой `<имя>_glow.png`. */
public final class HeavenRenderers {
	public static final ModelLayerLocation SHADOW = new ModelLayerLocation(Celestial.id("shadow"), "main");
	public static final ModelLayerLocation STORM = new ModelLayerLocation(Celestial.id("storm_spirit"), "main");

	private HeavenRenderers() {}

	public static void init() {
		ModelLayerRegistry.registerModelLayer(SHADOW, HeavenModels.Shadow::createLayer);
		ModelLayerRegistry.registerModelLayer(STORM, HeavenModels.Storm::createLayer);
		EntityRendererRegistry.register(ModEntities.SHADOW,
			ctx -> new Renderer<>(ctx, new HeavenModels.Shadow(ctx.bakeLayer(SHADOW)), "shadow", 0.4F, 1.0F));
		EntityRendererRegistry.register(ModEntities.STORM_SPIRIT,
			ctx -> new Renderer<>(ctx, new HeavenModels.Storm(ctx.bakeLayer(STORM)), "storm_spirit", 0.4F, 1.0F));
		EntityRendererRegistry.register(ModEntities.STORM_ELEMENTAL,
			ctx -> new Renderer<>(ctx, new HeavenModels.Storm(ctx.bakeLayer(STORM)), "storm_elemental", 1.0F, 2.2F));
	}

	static class Renderer<T extends Mob> extends MobRenderer<T, HeavenModels.State, EntityModel<HeavenModels.State>> {
		private final Identifier texture;
		private final float scale;

		Renderer(EntityRendererProvider.Context ctx, EntityModel<HeavenModels.State> model, String name, float shadow, float scale) {
			super(ctx, model, shadow);
			this.texture = Celestial.id("textures/entity/" + name + ".png");
			this.scale = scale;
			addLayer(new AbyssRenderers.GlowLayer<>(this, Celestial.id("textures/entity/" + name + "_glow.png")));
		}

		@Override
		public Identifier getTextureLocation(HeavenModels.State state) {
			return texture;
		}

		@Override
		public HeavenModels.State createRenderState() {
			return new HeavenModels.State();
		}

		@Override
		public void extractRenderState(T entity, HeavenModels.State state, float partialTicks) {
			super.extractRenderState(entity, state, partialTicks);
			state.attack = entity.getSwingAnimation(partialTicks);
		}

		@Override
		protected void scale(HeavenModels.State state, PoseStack poseStack) {
			poseStack.scale(scale, scale, scale);
		}
	}
}
