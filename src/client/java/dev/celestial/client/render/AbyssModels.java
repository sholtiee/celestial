package dev.celestial.client.render;

import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.util.Mth;

/** Модели существ Бездны: Слепой охотник, Светоед, Глубинный червь. Все со своей анимацией. */
public final class AbyssModels {
	private AbyssModels() {}

	/** Состояние для моделей Бездны: охота (охотник), сытость (светоед), фаза (червь). */
	public static class State extends LivingEntityRenderState {
		public boolean hunting;
		public int fullness;
		public int phase;
	}

	// ---------------------------------------------------------------- Слепой охотник (64×64)
	public static class BlindHunter extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart head;
		private final ModelPart leftArm;
		private final ModelPart rightArm;
		private final ModelPart leftLeg;
		private final ModelPart rightLeg;
		private final ModelPart leftFrill;
		private final ModelPart rightFrill;

		public BlindHunter(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.head = body.getChild("head");
			this.leftArm = body.getChild("left_arm");
			this.rightArm = body.getChild("right_arm");
			this.leftLeg = root.getChild("left_leg");
			this.rightLeg = root.getChild("right_leg");
			this.leftFrill = head.getChild("left_frill");
			this.rightFrill = head.getChild("right_frill");
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(0, 0).addBox(-5, -16, -3, 10, 16, 6),
				PartPose.offset(0, 8, 0));
			PartDefinition head = body.addOrReplaceChild("head", CubeListBuilder.create().texOffs(32, 0).addBox(-4, -8, -5, 8, 8, 8),
				PartPose.offset(0, -16, 0));
			head.addOrReplaceChild("left_frill", CubeListBuilder.create().texOffs(52, 16).addBox(0, -6, 0, 1, 7, 5),
				PartPose.offsetAndRotation(4, -5, -2, 0, 0.3F, 0));
			head.addOrReplaceChild("right_frill", CubeListBuilder.create().texOffs(52, 16).mirror().addBox(-1, -6, 0, 1, 7, 5),
				PartPose.offsetAndRotation(-4, -5, -2, 0, -0.3F, 0));
			body.addOrReplaceChild("left_arm", CubeListBuilder.create().texOffs(44, 28).addBox(-1, 0, -1.5F, 3, 22, 3),
				PartPose.offset(6, -15, 0));
			body.addOrReplaceChild("right_arm", CubeListBuilder.create().texOffs(32, 28).addBox(-2, 0, -1.5F, 3, 22, 3),
				PartPose.offset(-6, -15, 0));
			root.addOrReplaceChild("left_leg", CubeListBuilder.create().texOffs(16, 40).addBox(-2, 0, -2, 4, 16, 4), PartPose.offset(2.5F, 8, 0));
			root.addOrReplaceChild("right_leg", CubeListBuilder.create().texOffs(0, 40).addBox(-2, 0, -2, 4, 16, 4), PartPose.offset(-2.5F, 8, 0));
			return LayerDefinition.create(mesh, 64, 64);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float walk = state.walkAnimationPos * 0.6F;
			float amp = Math.min(1.0F, state.walkAnimationSpeed);
			float t = state.ageInTicks;
			body.xRot = state.hunting ? 0.25F : 0.55F;  // сутулится, а на охоте выпрямляется
			head.xRot = -body.xRot + 0.1F;
			head.yRot = state.hunting ? state.yRot * Mth.DEG_TO_RAD * 0.3F : Mth.sin(t * 0.9F) * 0.25F;  // «принюхивается»
			head.zRot = state.hunting ? 0 : Mth.sin(t * 1.7F) * 0.08F;
			float reach = state.hunting ? -1.1F : -0.45F;
			leftArm.xRot = reach + Mth.cos(walk) * 0.7F * amp + Mth.sin(t * 0.1F) * 0.05F;
			rightArm.xRot = reach - Mth.cos(walk) * 0.7F * amp - Mth.sin(t * 0.1F) * 0.05F;
			leftArm.zRot = -0.1F;
			rightArm.zRot = 0.1F;
			leftLeg.xRot = -Mth.cos(walk) * 0.9F * amp;
			rightLeg.xRot = Mth.cos(walk) * 0.9F * amp;
			float flare = state.hunting ? 0.9F + Mth.sin(t * 0.8F) * 0.15F : 0.3F;  // «слуховые» гребни раскрываются
			leftFrill.yRot = flare;
			rightFrill.yRot = -flare;
		}
	}

	// ---------------------------------------------------------------- Светоед (64×64)
	public static class LightEater extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart leftWing;
		private final ModelPart rightWing;
		private final ModelPart leftHind;
		private final ModelPart rightHind;
		private final ModelPart leftAntenna;
		private final ModelPart rightAntenna;

		public LightEater(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.leftWing = body.getChild("left_wing");
			this.rightWing = body.getChild("right_wing");
			this.leftHind = body.getChild("left_hind");
			this.rightHind = body.getChild("right_hind");
			this.leftAntenna = body.getChild("head").getChild("left_antenna");
			this.rightAntenna = body.getChild("head").getChild("right_antenna");
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(0, 0).addBox(-2, -2, -4, 4, 4, 8),
				PartPose.offset(0, 18, 0));
			PartDefinition head = body.addOrReplaceChild("head", CubeListBuilder.create().texOffs(24, 0).addBox(-2, -2, -3, 4, 4, 3),
				PartPose.offset(0, 0, -4));
			head.addOrReplaceChild("left_antenna", CubeListBuilder.create().texOffs(40, 0).addBox(-0.5F, -6, -0.5F, 3, 6, 1),
				PartPose.offsetAndRotation(1, -2, -2, -0.6F, 0, 0.35F));
			head.addOrReplaceChild("right_antenna", CubeListBuilder.create().texOffs(40, 0).mirror().addBox(-2.5F, -6, -0.5F, 3, 6, 1),
				PartPose.offsetAndRotation(-1, -2, -2, -0.6F, 0, -0.35F));
			body.addOrReplaceChild("abdomen", CubeListBuilder.create().texOffs(0, 12).addBox(-1.5F, -1.5F, 0, 3, 3, 5),
				PartPose.offsetAndRotation(0, 0.5F, 4, -0.25F, 0, 0));
			body.addOrReplaceChild("left_wing", CubeListBuilder.create().texOffs(0, 24).addBox(0, 0, -5, 12, 1, 9),
				PartPose.offset(2, -2, -1));
			body.addOrReplaceChild("right_wing", CubeListBuilder.create().texOffs(0, 34).addBox(-12, 0, -5, 12, 1, 9),
				PartPose.offset(-2, -2, -1));
			body.addOrReplaceChild("left_hind", CubeListBuilder.create().texOffs(0, 44).addBox(0, 0, 0, 8, 1, 6),
				PartPose.offset(2, -1.5F, 2));
			body.addOrReplaceChild("right_hind", CubeListBuilder.create().texOffs(0, 51).addBox(-8, 0, 0, 8, 1, 6),
				PartPose.offset(-2, -1.5F, 2));
			return LayerDefinition.create(mesh, 64, 64);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float t = state.ageInTicks;
			float flap = Mth.sin(t * 1.4F);
			leftWing.zRot = -0.15F - flap * 0.85F;
			rightWing.zRot = -leftWing.zRot;
			leftHind.zRot = -0.1F - Mth.sin(t * 1.4F - 0.6F) * 0.6F;
			rightHind.zRot = -leftHind.zRot;
			body.y = 18 + Mth.sin(t * 0.25F) * 1.5F;
			body.xRot = Mth.sin(t * 0.2F) * 0.1F;
			leftAntenna.xRot = -0.6F + Mth.sin(t * 0.3F) * 0.15F;
			rightAntenna.xRot = -0.6F + Mth.sin(t * 0.3F + 1) * 0.15F;
		}
	}

	// ---------------------------------------------------------------- Морозный дух (64×64)
	public static class FrostWraith extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart tail;
		private final ModelPart tip;
		private final ModelPart leftArm;
		private final ModelPart rightArm;

		public FrostWraith(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.tail = body.getChild("tail");
			this.tip = tail.getChild("tip");
			this.leftArm = body.getChild("left_arm");
			this.rightArm = body.getChild("right_arm");
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(0, 16).addBox(-4, 0, -2.5F, 8, 10, 5),
				PartPose.offset(0, 2, 0));
			body.addOrReplaceChild("hood", CubeListBuilder.create().texOffs(0, 0).addBox(-4, -8, -4, 8, 8, 8), PartPose.ZERO);
			PartDefinition tail = body.addOrReplaceChild("tail", CubeListBuilder.create().texOffs(0, 32).addBox(-3, 0, -2, 6, 8, 4),
				PartPose.offset(0, 10, 0));
			tail.addOrReplaceChild("tip", CubeListBuilder.create().texOffs(24, 32).addBox(-2, 0, -1.5F, 4, 6, 3), PartPose.offset(0, 8, 0));
			body.addOrReplaceChild("left_arm", CubeListBuilder.create().texOffs(32, 16).addBox(0, 0, -1, 2, 12, 2), PartPose.offset(4, 1, 0));
			body.addOrReplaceChild("right_arm", CubeListBuilder.create().texOffs(40, 16).addBox(-2, 0, -1, 2, 12, 2), PartPose.offset(-4, 1, 0));
			return LayerDefinition.create(mesh, 64, 64);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float t = state.ageInTicks;
			body.y = 2 + Mth.sin(t * 0.1F) * 1.2F;
			tail.xRot = 0.25F + Mth.sin(t * 0.12F) * 0.15F;
			tip.xRot = 0.3F + Mth.sin(t * 0.12F - 0.8F) * 0.25F;
			tail.zRot = Mth.sin(t * 0.07F) * 0.1F;
			leftArm.xRot = -0.9F + Mth.sin(t * 0.09F) * 0.2F;
			rightArm.xRot = -0.9F + Mth.sin(t * 0.09F + 1.5F) * 0.2F;
			leftArm.zRot = -0.25F;
			rightArm.zRot = 0.25F;
		}
	}

	// ---------------------------------------------------------------- Глубинный червь (128×128)
	public static class DeepWorm extends EntityModel<State> {
		private final ModelPart[] segments = new ModelPart[3];
		private final ModelPart head;
		private final ModelPart leftJaw;
		private final ModelPart rightJaw;

		public DeepWorm(ModelPart root) {
			super(root);
			ModelPart s = root.getChild("seg0");
			segments[0] = s;
			segments[1] = s.getChild("seg1");
			segments[2] = segments[1].getChild("seg2");
			this.head = segments[2].getChild("head");
			this.leftJaw = head.getChild("left_jaw");
			this.rightJaw = head.getChild("right_jaw");
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			// часть тела уходит в землю (ниже 24) — снизу червь «растёт» из камня
			PartDefinition s0 = root.addOrReplaceChild("seg0", CubeListBuilder.create().texOffs(0, 0).addBox(-7, -12, -7, 14, 28, 14),
				PartPose.offset(0, 24, 0));
			PartDefinition s1 = s0.addOrReplaceChild("seg1", CubeListBuilder.create().texOffs(56, 0).addBox(-6.5F, -11, -6.5F, 13, 11, 13),
				PartPose.offset(0, -12, 0));
			PartDefinition s2 = s1.addOrReplaceChild("seg2", CubeListBuilder.create().texOffs(56, 24).addBox(-6, -10, -6, 12, 10, 12),
				PartPose.offset(0, -11, 0));
			PartDefinition head = s2.addOrReplaceChild("head", CubeListBuilder.create().texOffs(0, 46).addBox(-7, -10, -7, 14, 10, 14),
				PartPose.offset(0, -10, 0));
			head.addOrReplaceChild("left_jaw", CubeListBuilder.create().texOffs(110, 0).addBox(-1, -9, -2, 3, 10, 4),
				PartPose.offset(5, -10, 0));
			head.addOrReplaceChild("right_jaw", CubeListBuilder.create().texOffs(110, 14).addBox(-2, -9, -2, 3, 10, 4),
				PartPose.offset(-5, -10, 0));
			return LayerDefinition.create(mesh, 128, 128);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float t = state.ageInTicks * 0.15F;
			for (int i = 0; i < segments.length; i++) {  // S-образный изгиб тела
				segments[i].xRot = Mth.sin(t - i * 0.9F) * 0.12F;
				segments[i].zRot = Mth.cos(t * 0.8F - i * 0.9F) * 0.1F;
			}
			boolean exposed = state.phase == dev.celestial.entity.DeepWorm.Phase.EXPOSED.ordinal();
			float chomp = exposed ? Math.max(0, Mth.sin(state.ageInTicks * 0.25F)) : 0.15F;  // жвалы раскрываются в укусе
			leftJaw.zRot = -0.2F - chomp * 0.7F;
			rightJaw.zRot = -leftJaw.zRot;
			head.xRot = exposed ? -0.2F : 0;
		}
	}
}
