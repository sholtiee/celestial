package dev.celestial.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.celestial.Celestial;
import dev.celestial.boss.FrostArchon;
import dev.celestial.boss.IceSpike;
import dev.celestial.entity.Inia;
import dev.celestial.registry.ModEntities;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.ThrownItemRenderer;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/** Морозный Архонт, его ледяные шипы, снаряды и освобождённая Иния. */
public final class ArchonRenderer {
	public static final ModelLayerLocation ARCHON = new ModelLayerLocation(Celestial.id("frost_archon"), "main");
	public static final ModelLayerLocation SPIKE = new ModelLayerLocation(Celestial.id("ice_spike"), "main");

	private ArchonRenderer() {}

	public static void init() {
		ModelLayerRegistry.registerModelLayer(ARCHON, Model::createLayer);
		ModelLayerRegistry.registerModelLayer(SPIKE, SpikeModel::createLayer);
		EntityRendererRegistry.register(ModEntities.FROST_ARCHON, Boss::new);
		EntityRendererRegistry.register(ModEntities.ICE_SPIKE, Spike::new);
		EntityRendererRegistry.register(ModEntities.FROST_SHARD, ctx -> new ThrownItemRenderer<>(ctx, 1.2F, true));
		EntityRendererRegistry.register(ModEntities.INIA, IniaRenderer::new);
	}

	public static class State extends LivingEntityRenderState {
		public int phase;
		public float cast;
	}

	// ---------------------------------------------------------------- модель Архонта (128×128)
	public static class Model extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart head;
		private final ModelPart leftArm;
		private final ModelPart rightArm;
		private final ModelPart cloak;
		private final ModelPart skirt;
		private final ModelPart[] shards = new ModelPart[6];

		public Model(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.head = body.getChild("head");
			this.leftArm = body.getChild("left_arm");
			this.rightArm = body.getChild("right_arm");
			this.cloak = body.getChild("cloak");
			this.skirt = body.getChild("skirt");
			for (int i = 0; i < 6; i++) {
				shards[i] = root.getChild("shard" + i);
			}
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			// корпус висит над землёй: подол заканчивается на ~0.3 блока выше ног
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(0, 0).addBox(-6, -14, -4, 12, 14, 8),
				PartPose.offset(0, -8, 0));
			PartDefinition skirt = body.addOrReplaceChild("skirt", CubeListBuilder.create().texOffs(0, 22).addBox(-7, 0, -5, 14, 20, 10), PartPose.ZERO);
			skirt.addOrReplaceChild("hem", CubeListBuilder.create().texOffs(48, 22).addBox(-5, 0, -4, 10, 8, 8), PartPose.offset(0, 20, 0));
			PartDefinition head = body.addOrReplaceChild("head", CubeListBuilder.create().texOffs(40, 0).addBox(-4, -8, -4, 8, 8, 8),
				PartPose.offset(0, -14, 0));
			head.addOrReplaceChild("crown", CubeListBuilder.create().texOffs(72, 0).addBox(-4.5F, -9.5F, -4.5F, 9, 2, 9), PartPose.ZERO);
			for (int i = 0; i < 5; i++) {
				float a = i / 5.0F * Mth.TWO_PI;
				float h = i == 0 ? 7 : 5;
				head.addOrReplaceChild("crown_spike" + i, CubeListBuilder.create().texOffs(108, 0).addBox(-0.5F, -h, -0.5F, 1, h, 1),
					PartPose.offsetAndRotation(Mth.sin(a) * 3.8F, -9.5F, -Mth.cos(a) * 3.8F, -Mth.cos(a) * 0.25F, 0, -Mth.sin(a) * 0.25F));
			}
			body.addOrReplaceChild("left_pauldron", CubeListBuilder.create().texOffs(84, 16).addBox(-1, -3, -5, 6, 4, 10),
				PartPose.offsetAndRotation(5, -13, 0, 0, 0, -0.25F));
			body.addOrReplaceChild("right_pauldron", CubeListBuilder.create().texOffs(84, 16).mirror().addBox(-5, -3, -5, 6, 4, 10),
				PartPose.offsetAndRotation(-5, -13, 0, 0, 0, 0.25F));
			body.addOrReplaceChild("left_arm", CubeListBuilder.create().texOffs(84, 30).addBox(-2, 0, -2, 4, 16, 4), PartPose.offset(8, -12, 0));
			PartDefinition right = body.addOrReplaceChild("right_arm", CubeListBuilder.create().texOffs(84, 30).mirror().addBox(-2, 0, -2, 4, 16, 4),
				PartPose.offset(-8, -12, 0));
			PartDefinition scepter = right.addOrReplaceChild("scepter", CubeListBuilder.create().texOffs(100, 30).addBox(-0.5F, -16, -0.5F, 1, 28, 1),
				PartPose.offsetAndRotation(0, 14, -1, 1.45F, 0, 0));
			scepter.addOrReplaceChild("scepter_head", CubeListBuilder.create().texOffs(104, 30).addBox(-1.5F, -4, -1.5F, 3, 4, 3),
				PartPose.offsetAndRotation(0, -16, 0, 0, Mth.PI / 4, 0));
			body.addOrReplaceChild("cloak", CubeListBuilder.create().texOffs(0, 64).addBox(-7, 0, 0, 14, 30, 1), PartPose.offset(0, -14, 4.2F));
			for (int i = 0; i < 6; i++) {
				root.addOrReplaceChild("shard" + i, CubeListBuilder.create().texOffs(116, 0).addBox(-1, -3, -1, 2, 6, 2), PartPose.ZERO);
			}
			return LayerDefinition.create(mesh, 128, 128);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float t = state.ageInTicks;
			body.y = -8 + Mth.sin(t * 0.08F) * 1.2F;  // парит
			head.yRot = state.yRot * Mth.DEG_TO_RAD;
			head.xRot = state.xRot * Mth.DEG_TO_RAD;
			cloak.xRot = 0.12F + Mth.sin(t * 0.1F) * 0.06F;
			skirt.xRot = Mth.sin(t * 0.07F) * 0.04F;
			float cast = state.cast;
			// в покое руки чуть разведены, скипетр смотрит вперёд; при заклинании — обе руки вверх
			leftArm.xRot = -0.15F - cast * 2.6F + Mth.sin(t * 0.09F) * 0.05F;
			leftArm.zRot = -0.25F - cast * 0.3F;
			rightArm.xRot = -0.45F - cast * 2.2F;
			rightArm.zRot = 0.2F + cast * 0.3F;
			float speed = state.phase == 3 ? 0.09F : state.phase == 2 ? 0.07F : 0.05F;
			float radius = 18 + state.phase * 2 + cast * 6;
			for (int i = 0; i < 6; i++) {
				float a = t * speed + i / 6.0F * Mth.TWO_PI;
				ModelPart s = shards[i];
				s.x = Mth.cos(a) * radius;
				s.z = Mth.sin(a) * radius;
				s.y = -24 + Mth.sin(t * 0.13F + i) * 4;
				s.yRot = -a;
				s.zRot = 0.4F;
			}
		}
	}

	static class Boss extends MobRenderer<FrostArchon, State, Model> {
		private static final Identifier TEXTURE = Celestial.id("textures/entity/frost_archon.png");

		Boss(EntityRendererProvider.Context ctx) {
			super(ctx, new Model(ctx.bakeLayer(ARCHON)), 1.6F);
			addLayer(new AbyssRenderers.GlowLayer<>(this, Celestial.id("textures/entity/frost_archon_glow.png")));
		}

		@Override
		public Identifier getTextureLocation(State state) {
			return TEXTURE;
		}

		@Override
		public State createRenderState() {
			return new State();
		}

		@Override
		public void extractRenderState(FrostArchon entity, State state, float partialTicks) {
			super.extractRenderState(entity, state, partialTicks);
			state.phase = entity.phase();
			state.cast = Math.min(1.0F, Math.max(0, entity.casting() - partialTicks) / 8.0F);
		}

		@Override
		protected void scale(State state, PoseStack poseStack) {
			poseStack.scale(1.35F, 1.35F, 1.35F);  // босс должен нависать над игроком: ~5 блоков с короной
		}
	}

	// ---------------------------------------------------------------- ледяной шип (64×32): три кристалла разной высоты
	public static class SpikeModel extends EntityModel<SpikeState> {
		private final ModelPart spikes;

		public SpikeModel(ModelPart root) {
			super(root, RenderTypes::entityTranslucent);
			this.spikes = root.getChild("spikes");
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition spikes = mesh.getRoot().addOrReplaceChild("spikes", CubeListBuilder.create(), PartPose.offset(0, 24, 0));
			spikes.addOrReplaceChild("main", CubeListBuilder.create().texOffs(0, 0).addBox(-3, -36, -3, 6, 36, 6),
				PartPose.rotation(0.08F, 0.3F, 0.05F));
			spikes.addOrReplaceChild("side1", CubeListBuilder.create().texOffs(24, 0).addBox(-2, -22, -2, 4, 22, 4),
				PartPose.offsetAndRotation(4, 0, 2, 0.25F, 0.8F, -0.35F));
			spikes.addOrReplaceChild("side2", CubeListBuilder.create().texOffs(40, 0).addBox(-1.5F, -16, -1.5F, 3, 16, 3),
				PartPose.offsetAndRotation(-4, 0, -1, -0.3F, -0.5F, 0.3F));
			return LayerDefinition.create(mesh, 64, 64);
		}

		@Override
		public void setupAnim(SpikeState state) {
			super.setupAnim(state);
			spikes.yScale = Math.max(0.01F, state.growth);
			spikes.xScale = spikes.zScale = 0.6F + 0.4F * state.growth;
		}
	}

	public static class SpikeState extends EntityRenderState {
		public float growth;
	}

	static class Spike extends EntityRenderer<IceSpike, SpikeState> {
		private static final Identifier TEXTURE = Celestial.id("textures/entity/ice_spike.png");
		private final SpikeModel model;

		Spike(EntityRendererProvider.Context ctx) {
			super(ctx);
			this.model = new SpikeModel(ctx.bakeLayer(SPIKE));
		}

		@Override
		public SpikeState createRenderState() {
			return new SpikeState();
		}

		@Override
		public void extractRenderState(IceSpike entity, SpikeState state, float partialTicks) {
			super.extractRenderState(entity, state, partialTicks);
			state.growth = entity.growth(partialTicks);
		}

		@Override
		public void submit(SpikeState state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
			if (state.growth > 0) {
				poseStack.pushPose();
				poseStack.scale(-1.0F, -1.0F, 1.0F);
				poseStack.translate(0.0F, -1.5F, 0.0F);
				collector.submitModel(model, state, poseStack, TEXTURE, state.lightCoords, OverlayTexture.NO_OVERLAY, state.outlineColor);
				poseStack.popPose();
			}
			super.submit(state, poseStack, collector, camera);
		}
	}

	// ---------------------------------------------------------------- Иния: человеческая модель + пара белых крыльев
	static class IniaRenderer extends CelestialRenderers.Humanoid<Inia> {
		IniaRenderer(EntityRendererProvider.Context ctx) {
			super(ctx, Celestial.id("textures/entity/inia.png"), 1.0F);
			addLayer(new Wings(this, ctx));
			addLayer(new AbyssRenderers.GlowLayer<>(this, Celestial.id("textures/entity/inia_glow.png")));
		}
	}

	static class Wings extends RenderLayer<HumanoidRenderState, HumanoidModel<HumanoidRenderState>> {
		private static final Identifier TEXTURE = Celestial.id("textures/entity/inia_wings.png");
		private final SeraphRenderer.WingPair wings;

		Wings(RenderLayerParent<HumanoidRenderState, HumanoidModel<HumanoidRenderState>> parent, EntityRendererProvider.Context ctx) {
			super(parent);
			this.wings = new SeraphRenderer.WingPair(ctx.bakeLayer(ModelLayers.ELYTRA), 0.9F, 0.25F, 0.0F);
		}

		@Override
		public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, HumanoidRenderState state, float yRot, float xRot) {
			poseStack.pushPose();
			poseStack.translate(0.0F, 0.0F, 0.1F);
			poseStack.scale(1.2F, 1.2F, 1.2F);
			renderColoredCutoutModel(wings, TEXTURE, poseStack, collector, light, state, -1, 1);
			poseStack.popPose();
		}
	}
}
