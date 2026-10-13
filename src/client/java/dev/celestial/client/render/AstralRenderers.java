package dev.celestial.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.celestial.Celestial;
import dev.celestial.entity.StarDevourer;
import dev.celestial.registry.ModEntities;
import java.util.function.Function;
import java.util.function.Supplier;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;

/** Рендеры существ Астрала: свои модели + светящийся слой; Пустотный скат — на модели Небесного ската. */
public final class AstralRenderers {
	private AstralRenderers() {}

	public static void init() {
		register(ModEntities.STAR_FISH, "star_fish", AstralModels.Fish::createLayer, AstralModels.Fish::new, 0.2F, 1.0F);
		register(ModEntities.STAR_DEVOURER, "star_devourer", AstralModels.Devourer::createLayer, AstralModels.Devourer::new, 0.5F, 1.2F);
		EntityRendererRegistry.register(ModEntities.VOID_RAY, ctx -> new CelestialRenderers.SimpleRenderer<>(ctx,
			new SkyRayModel(ctx.bakeLayer(ModModelLayers.SKY_RAY)), Celestial.id("textures/entity/void_ray.png"), 1.8F, 1.8F, true));
	}

	private static <T extends Mob> void register(EntityType<T> type, String name, Supplier<LayerDefinition> layer,
		Function<ModelPart, EntityModel<AstralModels.State>> model, float shadow, float scale) {
		ModelLayerLocation location = new ModelLayerLocation(Celestial.id(name), "main");
		ModelLayerRegistry.registerModelLayer(location, layer::get);
		EntityRendererRegistry.register(type, ctx -> new Renderer<>(ctx, model.apply(ctx.bakeLayer(location)), name, shadow, scale));
	}

	static class Renderer<T extends Mob> extends MobRenderer<T, AstralModels.State, EntityModel<AstralModels.State>> {
		private final Identifier texture;
		private final float scale;

		Renderer(EntityRendererProvider.Context ctx, EntityModel<AstralModels.State> model, String name, float shadow, float scale) {
			super(ctx, model, shadow);
			this.texture = Celestial.id("textures/entity/" + name + ".png");
			this.scale = scale;
			addLayer(new AbyssRenderers.GlowLayer<>(this, Celestial.id("textures/entity/" + name + "_glow.png")));
		}

		@Override
		public Identifier getTextureLocation(AstralModels.State state) {
			return texture;
		}

		@Override
		public AstralModels.State createRenderState() {
			return new AstralModels.State();
		}

		@Override
		public void extractRenderState(T entity, AstralModels.State state, float partialTicks) {
			super.extractRenderState(entity, state, partialTicks);
			state.bite = entity instanceof StarDevourer d ? d.biteProgress(partialTicks) : 0;
		}

		@Override
		protected void scale(AstralModels.State state, PoseStack poseStack) {
			poseStack.scale(scale, scale, scale);
		}
	}
}
