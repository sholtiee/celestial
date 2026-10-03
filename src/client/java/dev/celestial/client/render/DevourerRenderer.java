package dev.celestial.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.celestial.Celestial;
import dev.celestial.boss.LightDevourer;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/**
 * Пожиратель Света: огромный «скат тьмы» — тело, крылья из двух секций (волна от корня к краю), хвост из трёх
 * звеньев со светящимся жалом и пасть. Тёмные жилы светятся всегда, золотые — только когда он «проявлен» (горят ≥2 жаровни).
 */
public class DevourerRenderer extends MobRenderer<LightDevourer, DevourerRenderer.State, DevourerRenderer.Model> {
	public static final ModelLayerLocation LAYER = new ModelLayerLocation(Celestial.id("light_devourer"), "main");
	private static final Identifier TEXTURE = Celestial.id("textures/entity/light_devourer.png");

	public static class State extends LivingEntityRenderState {
		public boolean exposed;
	}

	public DevourerRenderer(EntityRendererProvider.Context ctx) {
		super(ctx, new Model(ctx.bakeLayer(LAYER)), 2.5F);
		addLayer(new AbyssRenderers.GlowLayer<>(this, Celestial.id("textures/entity/light_devourer_glow.png")));
		addLayer(new AbyssRenderers.GlowLayer<>(this, Celestial.id("textures/entity/light_devourer_exposed.png")) {
			@Override
			public void submit(PoseStack pose, SubmitNodeCollector collector, int light, State state, float yRot, float xRot) {
				if (state.exposed) {
					super.submit(pose, collector, light, state, yRot, xRot);
				}
			}
		});
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
	public void extractRenderState(LightDevourer entity, State state, float partialTicks) {
		super.extractRenderState(entity, state, partialTicks);
		state.exposed = entity.exposed();
	}

	@Override
	protected float getFlipDegrees() {
		return 0;
	}

	public static class Model extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart jaw;
		private final ModelPart leftInner;
		private final ModelPart leftOuter;
		private final ModelPart rightInner;
		private final ModelPart rightOuter;
		private final ModelPart[] tail = new ModelPart[3];

		public Model(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.jaw = body.getChild("head").getChild("jaw");
			this.leftInner = body.getChild("left_wing");
			this.leftOuter = leftInner.getChild("tip");
			this.rightInner = body.getChild("right_wing");
			this.rightOuter = rightInner.getChild("tip");
			tail[0] = body.getChild("tail0");
			tail[1] = tail[0].getChild("tail1");
			tail[2] = tail[1].getChild("tail2");
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(0, 0).addBox(-10, -3, -14, 20, 6, 28),
				PartPose.offset(0, 12, 0));
			PartDefinition head = body.addOrReplaceChild("head", CubeListBuilder.create().texOffs(96, 0).addBox(-6, -3, -8, 12, 6, 8),
				PartPose.offset(0, 0, -14));
			head.addOrReplaceChild("jaw", CubeListBuilder.create().texOffs(136, 0).addBox(-5, 0, -7, 10, 2, 7), PartPose.offset(0, 2, -1));
			PartDefinition lw = body.addOrReplaceChild("left_wing", CubeListBuilder.create().texOffs(0, 34).addBox(0, -1, -12, 18, 2, 24),
				PartPose.offset(10, 0, -2));
			lw.addOrReplaceChild("tip", CubeListBuilder.create().texOffs(96, 34).addBox(0, -0.5F, -10, 16, 1, 20), PartPose.offset(18, 0, 0));
			PartDefinition rw = body.addOrReplaceChild("right_wing", CubeListBuilder.create().texOffs(0, 60).addBox(-18, -1, -12, 18, 2, 24),
				PartPose.offset(-10, 0, -2));
			rw.addOrReplaceChild("tip", CubeListBuilder.create().texOffs(96, 56).addBox(-16, -0.5F, -10, 16, 1, 20), PartPose.offset(-18, 0, 0));
			PartDefinition t0 = body.addOrReplaceChild("tail0", CubeListBuilder.create().texOffs(0, 86).addBox(-3, -2, 0, 6, 4, 12),
				PartPose.offset(0, 0, 14));
			PartDefinition t1 = t0.addOrReplaceChild("tail1", CubeListBuilder.create().texOffs(40, 86).addBox(-2, -1.5F, 0, 4, 3, 12),
				PartPose.offset(0, 0, 12));
			t1.addOrReplaceChild("tail2", CubeListBuilder.create().texOffs(76, 86).addBox(-1, -1, 0, 2, 2, 10)
				.texOffs(104, 86).addBox(-2, -2, 10, 4, 4, 4), PartPose.offset(0, 0, 12));
			return LayerDefinition.create(mesh, 256, 128);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float t = state.ageInTicks * 0.18F;
			leftInner.zRot = Mth.sin(t) * 0.35F;
			leftOuter.zRot = Mth.sin(t - 0.9F) * 0.55F;
			rightInner.zRot = -leftInner.zRot;
			rightOuter.zRot = -leftOuter.zRot;
			for (int i = 0; i < tail.length; i++) {
				tail[i].yRot = Mth.sin(t * 0.6F - i * 0.8F) * 0.28F;
				tail[i].xRot = Mth.cos(t * 0.5F - i * 0.7F) * 0.08F;
			}
			body.xRot = Mth.sin(t * 0.4F) * 0.06F;
			jaw.xRot = 0.15F + Math.max(0, Mth.sin(state.ageInTicks * 0.07F)) * 0.45F;
		}
	}
}
