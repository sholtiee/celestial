package dev.celestial.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.celestial.Celestial;
import dev.celestial.boss.Faceless;
import dev.celestial.registry.ModEntities;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.ThrownItemRenderer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/**
 * Безликий: фигура в тёмном балахоне, под капюшоном — пустота вместо лица; шесть рваных крыльев (он был Серафимом, Ис. 6:2),
 * вокруг — кольцо погасших звёзд. В седьмой трубе на груди проступает утренняя звезда; повергнутый — склоняет голову, крылья опущены.
 */
public final class FacelessRenderer {
	public static final ModelLayerLocation LAYER = new ModelLayerLocation(Celestial.id("faceless"), "main");
	private static final int STARS = 12;

	private FacelessRenderer() {}

	public static void init() {
		ModelLayerRegistry.registerModelLayer(LAYER, Model::createLayer);
		EntityRendererRegistry.register(ModEntities.FACELESS, Boss::new);
		EntityRendererRegistry.register(ModEntities.VOID_BOLT, ctx -> new ThrownItemRenderer<>(ctx, 1.4F, true));
	}

	public static class State extends LivingEntityRenderState {
		public int phase;
		public boolean defeated;
		public float cast;
	}

	public static class Model extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart head;
		private final ModelPart leftArm;
		private final ModelPart rightArm;
		private final ModelPart robe;
		private final ModelPart star;
		private final ModelPart[] wings = new ModelPart[6];
		private final ModelPart ring;

		public Model(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.head = body.getChild("head");
			this.leftArm = body.getChild("left_arm");
			this.rightArm = body.getChild("right_arm");
			this.robe = body.getChild("robe");
			this.star = body.getChild("star");
			for (int i = 0; i < 6; i++) {
				wings[i] = body.getChild("wing" + i);
			}
			this.ring = root.getChild("ring");
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(0, 0).addBox(-5, -14, -3, 10, 14, 6),
				PartPose.offset(0, -10, 0));
			body.addOrReplaceChild("robe", CubeListBuilder.create().texOffs(0, 20).addBox(-6, 0, -4, 12, 22, 8), PartPose.ZERO);
			PartDefinition head = body.addOrReplaceChild("head", CubeListBuilder.create().texOffs(40, 0).addBox(-4.5F, -9, -4.5F, 9, 9, 9),
				PartPose.offset(0, -14, 0));
			head.addOrReplaceChild("hood_tip", CubeListBuilder.create().texOffs(76, 0).addBox(-3, -3, -1, 6, 3, 6), PartPose.offsetAndRotation(0, -8, 1, 0.5F, 0, 0));
			body.addOrReplaceChild("left_arm", CubeListBuilder.create().texOffs(40, 20).addBox(-1.5F, 0, -1.5F, 3, 18, 3), PartPose.offset(6.5F, -13, 0));
			body.addOrReplaceChild("right_arm", CubeListBuilder.create().texOffs(40, 20).mirror().addBox(-1.5F, 0, -1.5F, 3, 18, 3), PartPose.offset(-6.5F, -13, 0));
			body.addOrReplaceChild("star", CubeListBuilder.create().texOffs(56, 20).addBox(-1.5F, -1.5F, -0.5F, 3, 3, 1), PartPose.offset(0, -8, -3.4F));
			// шесть крыльев — плоские рваные полотна от спины: верхняя пара вверх, средняя в стороны, нижняя вниз
			for (int i = 0; i < 6; i++) {
				boolean left = i % 2 == 0;
				body.addOrReplaceChild("wing" + i, CubeListBuilder.create().texOffs(0, 64).addBox(left ? 0 : -24, -8, 0, 24, 16, 1),
					PartPose.offset(left ? 2 : -2, -11 + (i / 2) * 4, 3.5F));
			}
			PartDefinition ring = root.addOrReplaceChild("ring", CubeListBuilder.create(), PartPose.offset(0, -6, 0));
			for (int i = 0; i < STARS; i++) {
				float a = i * Mth.TWO_PI / STARS;
				ring.addOrReplaceChild("star" + i, CubeListBuilder.create().texOffs(64, 20).addBox(-1, -1, -1, 2, 2, 2),
					PartPose.offset(Mth.cos(a) * 20, 0, Mth.sin(a) * 20));
			}
			return LayerDefinition.create(mesh, 128, 128);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float t = state.ageInTicks;
			float down = state.defeated ? 1.0F : 0.0F;
			body.y = -10 + Mth.sin(t * 0.05F) * 1.2F + down * 6;
			body.xRot = down * 0.35F;
			head.xRot = down * 0.6F + state.xRot * Mth.DEG_TO_RAD * (1 - down) * 0.5F;
			robe.xRot = Mth.sin(t * 0.06F) * 0.05F;
			float cast = state.cast;
			leftArm.zRot = -0.25F - cast * 1.2F + Mth.sin(t * 0.07F) * 0.05F;
			rightArm.zRot = 0.25F + cast * 1.2F - Mth.sin(t * 0.07F) * 0.05F;
			leftArm.xRot = rightArm.xRot = -cast * 0.8F - down * 0.4F;
			for (int i = 0; i < 6; i++) {
				boolean left = i % 2 == 0;
				int pair = i / 2;  // 0 верх, 1 середина, 2 низ
				float spread = (pair == 0 ? -0.55F : pair == 1 ? 0.0F : 0.55F) * (1 - down * 0.8F) + down * 0.9F;
				float flap = Mth.sin(t * 0.08F + pair) * 0.15F * (1 - down);
				wings[i].zRot = (left ? -1 : 1) * (spread + flap);
				wings[i].yRot = (left ? -1 : 1) * (0.45F + down * 0.4F);
			}
			star.visible = state.phase >= Faceless.TRUMPETS;
			ring.yRot = t * (state.defeated ? 0.002F : 0.01F + state.phase * 0.002F);
			ring.y = -6 + Mth.sin(t * 0.03F) * 2;
		}
	}

	static class Boss extends MobRenderer<Faceless, State, Model> {
		private static final Identifier TEXTURE = Celestial.id("textures/entity/faceless.png");

		Boss(EntityRendererProvider.Context ctx) {
			super(ctx, new Model(ctx.bakeLayer(LAYER)), 1.6F);
			addLayer(new AbyssRenderers.GlowLayer<>(this, Celestial.id("textures/entity/faceless_glow.png")));
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
		public void extractRenderState(Faceless entity, State state, float partialTicks) {
			super.extractRenderState(entity, state, partialTicks);
			state.phase = entity.phase();
			state.defeated = entity.defeated();
			state.cast = Math.min(1.0F, Math.max(0, entity.casting() - partialTicks) / 10.0F);
		}

		@Override
		protected void scale(State state, PoseStack poseStack) {
			poseStack.scale(1.4F, 1.4F, 1.4F);
		}
	}
}
