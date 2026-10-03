package dev.celestial.client.render;

import dev.celestial.Celestial;
import dev.celestial.entity.FallenGuardian;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/**
 * Падший страж: человекоподобная основа + шлем с гребнем, наплечники, плащ (колышется на ходу)
 * и надломленный нимб, косо висящий над головой. Глаза и обломок нимба светятся.
 */
public class GuardianRenderer extends HumanoidMobRenderer<FallenGuardian, HumanoidRenderState, GuardianRenderer.Model> {
	public static final ModelLayerLocation LAYER = new ModelLayerLocation(Celestial.id("fallen_guardian"), "main");
	private static final Identifier TEXTURE = Celestial.id("textures/entity/fallen_guardian.png");

	public GuardianRenderer(EntityRendererProvider.Context ctx) {
		super(ctx, new Model(ctx.bakeLayer(LAYER)), 0.5F);
		addLayer(new AbyssRenderers.GlowLayer<>(this, Celestial.id("textures/entity/fallen_guardian_glow.png")));
	}

	public static void register() {
		ModelLayerRegistry.registerModelLayer(LAYER, Model::createLayer);
	}

	@Override
	public Identifier getTextureLocation(HumanoidRenderState state) {
		return TEXTURE;
	}

	@Override
	public HumanoidRenderState createRenderState() {
		return new HumanoidRenderState();
	}

	public static class Model extends HumanoidModel<HumanoidRenderState> {
		private final ModelPart cape;
		private final ModelPart halo;

		public Model(ModelPart root) {
			super(root);
			this.cape = root.getChild("body").getChild("cape");
			this.halo = root.getChild("head").getChild("halo");
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = HumanoidModel.createMesh(CubeDeformation.NONE, 0.0F);
			PartDefinition root = mesh.getRoot();
			PartDefinition head = root.getChild("head");
			PartDefinition body = root.getChild("body");
			// гребень шлема
			head.addOrReplaceChild("crest", CubeListBuilder.create().texOffs(44, 32).addBox(-0.5F, -12, -3, 1, 4, 7), PartPose.ZERO);
			// надломленный нимб: три дуги из четырёх (четвёртой нет) — над головой с наклоном
			head.addOrReplaceChild("halo", CubeListBuilder.create()
				.texOffs(0, 48).addBox(-5, 0, -5, 10, 1, 1)
				.texOffs(0, 50).addBox(-5, 0, 4, 7, 1, 1)
				.texOffs(0, 52).addBox(-5, 0, -4, 1, 1, 8), PartPose.offsetAndRotation(0, -10.0F, 0, 0.22F, 0, 0.16F));
			// наплечники
			body.addOrReplaceChild("left_pauldron", CubeListBuilder.create().texOffs(24, 32).addBox(-1, -2, -2.5F, 5, 3, 5),
				PartPose.offset(5, 0.5F, 0));
			body.addOrReplaceChild("right_pauldron", CubeListBuilder.create().texOffs(24, 32).mirror().addBox(-4, -2, -2.5F, 5, 3, 5),
				PartPose.offset(-5, 0.5F, 0));
			// плащ, закреплён у плеч, висит за спиной
			body.addOrReplaceChild("cape", CubeListBuilder.create().texOffs(0, 32).addBox(-5, 0, 0, 10, 14, 1), PartPose.offset(0, 0.5F, 2.5F));
			return LayerDefinition.create(mesh, 64, 64);
		}

		@Override
		public void setupAnim(HumanoidRenderState state) {
			super.setupAnim(state);
			float speed = Math.min(1.0F, state.walkAnimationSpeed);
			cape.xRot = 0.08F + speed * 0.55F + Mth.sin(state.ageInTicks * 0.09F) * 0.04F;
			halo.y = -10.0F + Mth.sin(state.ageInTicks * 0.12F) * 0.4F;
			halo.yRot = state.ageInTicks * 0.02F;
		}
	}
}
