package dev.celestial.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.celestial.Celestial;
import dev.celestial.entity.CloudWhale;
import dev.celestial.entity.LightWisp;
import dev.celestial.entity.Pegasus;
import dev.celestial.entity.StormSpirit;
import dev.celestial.registry.ModEntities;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.animal.equine.BabyHorseModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.AbstractHorseRenderer;
import net.minecraft.client.renderer.entity.BlazeRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.PhantomRenderer;
import net.minecraft.client.renderer.entity.layers.SimpleEquipmentLayer;
import net.minecraft.client.renderer.entity.state.EquineRenderState;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.entity.state.PhantomRenderState;
import net.minecraft.client.model.animal.equine.EquineSaddleModel;
import net.minecraft.client.resources.model.EquipmentClientInfo;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Mob;

public final class CelestialRenderers {
	private CelestialRenderers() {}

	private static Identifier tex(String name) {
		return Celestial.id("textures/entity/" + name + ".png");
	}

	public static void init() {
		ModModelLayers.init();
		EntityRendererRegistry.register(ModEntities.FALLEN_GUARDIAN, ctx -> new Humanoid<>(ctx, tex("fallen_guardian"), 1.0F));
		EntityRendererRegistry.register(ModEntities.ANGEL, ctx -> new Humanoid<>(ctx, tex("angel"), 0.95F));
		EntityRendererRegistry.register(ModEntities.STORM_SPIRIT, StormSpiritRenderer::new);
		EntityRendererRegistry.register(ModEntities.WINGED_SERPENT, ctx -> new PhantomRenderer(ctx) {
			@Override
			public Identifier getTextureLocation(PhantomRenderState state) {
				return tex("winged_serpent");
			}
		});
		EntityRendererRegistry.register(ModEntities.CLOUD_WHALE, CloudWhaleRenderer::new);
		EntityRendererRegistry.register(ModEntities.LIGHT_WISP, LightWispRenderer::new);
		EntityRendererRegistry.register(ModEntities.PEGASUS, PegasusRenderer::new);
	}

	/** Человекоподобные мобы Рая на общей модели 64×64. Крылья рисует ванильный WingsLayer по предмету в слоте груди. */
	public static class Humanoid<T extends Mob> extends HumanoidMobRenderer<T, HumanoidRenderState, HumanoidModel<HumanoidRenderState>> {
		private final Identifier texture;
		private final float scale;

		public Humanoid(EntityRendererProvider.Context ctx, Identifier texture, float scale) {
			super(ctx, new HumanoidModel<>(ctx.bakeLayer(ModModelLayers.HUMANOID)), 0.5F);
			this.texture = texture;
			this.scale = scale;
		}

		@Override
		public Identifier getTextureLocation(HumanoidRenderState state) {
			return texture;
		}

		@Override
		public HumanoidRenderState createRenderState() {
			return new HumanoidRenderState();
		}

		@Override
		protected void scale(HumanoidRenderState state, PoseStack poseStack) {
			poseStack.scale(scale, scale, scale);
		}
	}

	static class StormSpiritRenderer extends BlazeRenderer {
		StormSpiritRenderer(EntityRendererProvider.Context ctx) {
			super(ctx);
		}

		@Override
		public Identifier getTextureLocation(LivingEntityRenderState state) {
			return tex("storm_spirit");
		}
	}

	static class CloudWhaleRenderer extends MobRenderer<CloudWhale, LivingEntityRenderState, CloudWhaleModel> {
		CloudWhaleRenderer(EntityRendererProvider.Context ctx) {
			super(ctx, new CloudWhaleModel(ctx.bakeLayer(ModModelLayers.CLOUD_WHALE)), 2.5F);
		}

		@Override
		public Identifier getTextureLocation(LivingEntityRenderState state) {
			return tex("cloud_whale");
		}

		@Override
		public LivingEntityRenderState createRenderState() {
			return new LivingEntityRenderState();
		}

		@Override
		protected void scale(LivingEntityRenderState state, PoseStack poseStack) {
			poseStack.scale(2.0F, 2.0F, 2.0F);
		}
	}

	static class LightWispRenderer extends MobRenderer<LightWisp, LivingEntityRenderState, LightWispModel> {
		LightWispRenderer(EntityRendererProvider.Context ctx) {
			super(ctx, new LightWispModel(ctx.bakeLayer(ModModelLayers.LIGHT_WISP)), 0.15F);
		}

		@Override
		public Identifier getTextureLocation(LivingEntityRenderState state) {
			return tex("light_wisp");
		}

		@Override
		public LivingEntityRenderState createRenderState() {
			return new LivingEntityRenderState();
		}

		@Override
		protected int getBlockLightLevel(LightWisp entity, BlockPos pos) {
			return 15;
		}
	}

	static class PegasusRenderer extends AbstractHorseRenderer<Pegasus, EquineRenderState, net.minecraft.client.model.EntityModel<EquineRenderState>> {
		PegasusRenderer(EntityRendererProvider.Context ctx) {
			super(ctx, new PegasusModel(ctx.bakeLayer(ModModelLayers.PEGASUS)), new BabyHorseModel(ctx.bakeLayer(ModelLayers.HORSE_BABY)));
			this.addLayer(new SimpleEquipmentLayer<>(this, ctx.getEquipmentRenderer(), EquipmentClientInfo.LayerType.HORSE_SADDLE,
				state -> state.saddle, new EquineSaddleModel(ctx.bakeLayer(ModelLayers.HORSE_SADDLE)), null, 2));
		}

		@Override
		public Identifier getTextureLocation(EquineRenderState state) {
			return state.isBaby ? tex("pegasus_baby") : tex("pegasus");
		}

		@Override
		public EquineRenderState createRenderState() {
			return new EquineRenderState();
		}
	}
}
