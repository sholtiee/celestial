package dev.celestial.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.celestial.Celestial;
import dev.celestial.entity.IceGuardian;
import dev.celestial.entity.IceWolf;
import dev.celestial.registry.ModEntities;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Mob;

/** Рендеры существ Ледяных Чертогов: свои модели + светящийся слой `<имя>_glow.png`. */
public final class FrozenRenderers {
	public static final ModelLayerLocation ICE_GUARDIAN = new ModelLayerLocation(Celestial.id("ice_guardian"), "main");
	public static final ModelLayerLocation ICE_WOLF = new ModelLayerLocation(Celestial.id("ice_wolf"), "main");

	private FrozenRenderers() {}

	public static void init() {
		ModelLayerRegistry.registerModelLayer(ICE_GUARDIAN, FrozenModels.IceGuardian::createLayer);
		ModelLayerRegistry.registerModelLayer(ICE_WOLF, FrozenModels.IceWolf::createLayer);
		EntityRendererRegistry.register(ModEntities.ICE_GUARDIAN,
			ctx -> new Renderer<>(ctx, new FrozenModels.IceGuardian(ctx.bakeLayer(ICE_GUARDIAN)), "ice_guardian", 1.0F, 1.0F));
		EntityRendererRegistry.register(ModEntities.ICE_WOLF,
			ctx -> new Renderer<>(ctx, new FrozenModels.IceWolf(ctx.bakeLayer(ICE_WOLF)), "ice_wolf", 0.7F, 1.0F));
	}

	static class Renderer<T extends Mob> extends MobRenderer<T, FrozenModels.State, EntityModel<FrozenModels.State>> {
		private final Identifier texture;
		private final float scale;

		Renderer(EntityRendererProvider.Context ctx, EntityModel<FrozenModels.State> model, String name, float shadow, float scale) {
			super(ctx, model, shadow);
			this.texture = Celestial.id("textures/entity/" + name + ".png");
			this.scale = scale;
			addLayer(new AbyssRenderers.GlowLayer<>(this, Celestial.id("textures/entity/" + name + "_glow.png")));
		}

		@Override
		public Identifier getTextureLocation(FrozenModels.State state) {
			return texture;
		}

		@Override
		public FrozenModels.State createRenderState() {
			return new FrozenModels.State();
		}

		@Override
		public void extractRenderState(T entity, FrozenModels.State state, float partialTicks) {
			super.extractRenderState(entity, state, partialTicks);
			if (entity instanceof IceGuardian guardian) {
				state.attack = guardian.attackProgress(partialTicks);
				state.slam = guardian.slamProgress(partialTicks);
				state.shield = guardian.shielded();
			} else if (entity instanceof IceWolf wolf) {
				state.saddled = wolf.isSaddled();
				state.ridden = wolf.isVehicle();
			}
		}

		@Override
		protected void scale(FrozenModels.State state, PoseStack poseStack) {
			float s = state.isBaby ? scale * 0.5F : scale;
			poseStack.scale(s, s, s);
		}
	}
}
