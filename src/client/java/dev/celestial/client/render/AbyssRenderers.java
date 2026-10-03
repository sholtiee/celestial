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
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.EyesLayer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Mob;

/** Рендеры существ Бездны: свои модели + светящийся слой (глаза, споры, кристаллы). */
public final class AbyssRenderers {
	public static final ModelLayerLocation BLIND_HUNTER = layer("blind_hunter");
	public static final ModelLayerLocation LIGHT_EATER = layer("light_eater");
	public static final ModelLayerLocation DEEP_WORM = layer("deep_worm");
	public static final ModelLayerLocation FROST_WRAITH = layer("frost_wraith");

	private AbyssRenderers() {}

	private static ModelLayerLocation layer(String name) {
		return new ModelLayerLocation(Celestial.id(name), "main");
	}

	private static Identifier tex(String name) {
		return Celestial.id("textures/entity/" + name + ".png");
	}

	public static void init() {
		ModelLayerRegistry.registerModelLayer(BLIND_HUNTER, AbyssModels.BlindHunter::createLayer);
		ModelLayerRegistry.registerModelLayer(LIGHT_EATER, AbyssModels.LightEater::createLayer);
		ModelLayerRegistry.registerModelLayer(DEEP_WORM, AbyssModels.DeepWorm::createLayer);
		ModelLayerRegistry.registerModelLayer(FROST_WRAITH, AbyssModels.FrostWraith::createLayer);
		EntityRendererRegistry.register(ModEntities.FROST_WRAITH,
			ctx -> new Renderer<>(ctx, new AbyssModels.FrostWraith(ctx.bakeLayer(FROST_WRAITH)), "frost_wraith", 0.3F, 1.0F));
		ModelLayerRegistry.registerModelLayer(DevourerRenderer.LAYER, DevourerRenderer.Model::createLayer);
		EntityRendererRegistry.register(ModEntities.LIGHT_DEVOURER, DevourerRenderer::new);
		EntityRendererRegistry.register(ModEntities.BLIND_HUNTER,
			ctx -> new Renderer<>(ctx, new AbyssModels.BlindHunter(ctx.bakeLayer(BLIND_HUNTER)), "blind_hunter", 0.7F, 1.0F));
		EntityRendererRegistry.register(ModEntities.LIGHT_EATER,
			ctx -> new Renderer<>(ctx, new AbyssModels.LightEater(ctx.bakeLayer(LIGHT_EATER)), "light_eater", 0.3F, 1.0F));
		EntityRendererRegistry.register(ModEntities.DEEP_WORM,
			ctx -> new Renderer<>(ctx, new AbyssModels.DeepWorm(ctx.bakeLayer(DEEP_WORM)), "deep_worm", 1.2F, 1.0F));
	}

	/** Светящийся слой: текстура `<имя>_glow.png` рисуется без затенения (как глаза паука или эндермена). */
	public static class GlowLayer<S extends LivingEntityRenderState, M extends EntityModel<S>> extends EyesLayer<S, M> {
		private final RenderType type;

		public GlowLayer(RenderLayerParent<S, M> parent, Identifier texture) {
			super(parent);
			this.type = RenderTypes.eyes(texture);
		}

		@Override
		public RenderType renderType() {
			return type;
		}
	}

	static class Renderer<T extends Mob> extends MobRenderer<T, AbyssModels.State, EntityModel<AbyssModels.State>> {
		private final Identifier texture;
		private final float scale;

		Renderer(EntityRendererProvider.Context ctx, EntityModel<AbyssModels.State> model, String name, float shadow, float scale) {
			super(ctx, model, shadow);
			this.texture = tex(name);
			this.scale = scale;
			addLayer(new GlowLayer<>(this, tex(name + "_glow")));
		}

		@Override
		public Identifier getTextureLocation(AbyssModels.State state) {
			return texture;
		}

		@Override
		public AbyssModels.State createRenderState() {
			return new AbyssModels.State();
		}

		@Override
		public void extractRenderState(T entity, AbyssModels.State state, float partialTicks) {
			super.extractRenderState(entity, state, partialTicks);
			if (entity instanceof dev.celestial.entity.BlindHunter hunter) {
				state.hunting = hunter.isHunting();
			} else if (entity instanceof dev.celestial.entity.LightEater eater) {
				state.fullness = eater.fullness();
			} else if (entity instanceof dev.celestial.entity.DeepWorm worm) {
				state.phase = worm.phase().ordinal();
			}
		}

		@Override
		protected void scale(AbyssModels.State state, PoseStack poseStack) {
			poseStack.scale(scale, scale, scale);
		}
	}
}
