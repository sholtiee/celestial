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

/** Модели существ Ледяных Чертогов. Развёртки текстур совпадают с texOffs (рисует tools/gen_frozen_mobs.py). */
public final class FrozenModels {
	private FrozenModels() {}

	public static class State extends LivingEntityRenderState {
		public float attack;
		public float slam;
		public boolean shield;
		public boolean saddled;
		public boolean ridden;
	}

	// ---------------------------------------------------------------- Ледяной страж (128×64)
	public static class IceGuardian extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart head;
		private final ModelPart leftArm;
		private final ModelPart rightArm;
		private final ModelPart leftLeg;
		private final ModelPart rightLeg;
		private final ModelPart core;
		private final ModelPart[] shards = new ModelPart[4];

		public IceGuardian(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.head = body.getChild("head");
			this.core = body.getChild("core");
			this.leftArm = body.getChild("left_arm");
			this.rightArm = body.getChild("right_arm");
			this.leftLeg = root.getChild("left_leg");
			this.rightLeg = root.getChild("right_leg");
			for (int i = 0; i < 4; i++) {
				shards[i] = root.getChild("shard" + i);
			}
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create()
					.texOffs(0, 0).addBox(-10, -20, -6, 20, 14, 12)
					.texOffs(22, 26).addBox(-6, -6, -4, 12, 6, 8),
				PartPose.offset(0, 10, 0));
			body.addOrReplaceChild("core", CubeListBuilder.create().texOffs(64, 0).addBox(-2.5F, -16, -6.8F, 5, 5, 1), PartPose.ZERO);
			PartDefinition head = body.addOrReplaceChild("head", CubeListBuilder.create().texOffs(96, 0).addBox(-4, -8, -4, 8, 8, 8),
				PartPose.offset(0, -20, -2));
			head.addOrReplaceChild("crest_mid", CubeListBuilder.create().texOffs(76, 0).addBox(-1, -6, -1, 2, 6, 2),
				PartPose.offsetAndRotation(0, -8, 0, -0.15F, 0, 0));
			head.addOrReplaceChild("crest_left", CubeListBuilder.create().texOffs(76, 0).addBox(-1, -6, -1, 2, 6, 2),
				PartPose.offsetAndRotation(3, -7, 1, -0.3F, 0, 0.45F));
			head.addOrReplaceChild("crest_right", CubeListBuilder.create().texOffs(76, 0).mirror().addBox(-1, -6, -1, 2, 6, 2),
				PartPose.offsetAndRotation(-3, -7, 1, -0.3F, 0, -0.45F));
			body.addOrReplaceChild("left_spike", CubeListBuilder.create().texOffs(84, 0).addBox(-1.5F, -8, -1.5F, 3, 8, 3),
				PartPose.offsetAndRotation(7, -19, 1, 0.2F, 0, 0.35F));
			body.addOrReplaceChild("right_spike", CubeListBuilder.create().texOffs(84, 0).mirror().addBox(-1.5F, -8, -1.5F, 3, 8, 3),
				PartPose.offsetAndRotation(-7, -19, 1, 0.2F, 0, -0.35F));
			body.addOrReplaceChild("left_arm", CubeListBuilder.create().texOffs(64, 16).addBox(0, -2, -3, 6, 26, 6),
				PartPose.offset(10, -17, 0));
			body.addOrReplaceChild("right_arm", CubeListBuilder.create().texOffs(88, 16).addBox(-6, -2, -3, 6, 26, 6),
				PartPose.offset(-10, -17, 0));
			root.addOrReplaceChild("left_leg", CubeListBuilder.create().texOffs(0, 44).addBox(-3, 0, -3, 6, 14, 6), PartPose.offset(5, 10, 0));
			root.addOrReplaceChild("right_leg", CubeListBuilder.create().texOffs(0, 44).mirror().addBox(-3, 0, -3, 6, 14, 6), PartPose.offset(-5, 10, 0));
			for (int i = 0; i < 4; i++) {
				root.addOrReplaceChild("shard" + i, CubeListBuilder.create().texOffs(0, 26).addBox(-5, -8, -0.5F, 10, 16, 1), PartPose.ZERO);
			}
			return LayerDefinition.create(mesh, 128, 64);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float walk = state.walkAnimationPos * 0.45F;
			float amp = Math.min(1.0F, state.walkAnimationSpeed);
			float t = state.ageInTicks;
			head.yRot = state.yRot * Mth.DEG_TO_RAD;
			head.xRot = state.xRot * Mth.DEG_TO_RAD;
			body.yRot = Mth.sin(walk) * 0.08F * amp;
			body.zRot = Mth.cos(walk) * 0.04F * amp;
			leftLeg.xRot = -Mth.cos(walk) * 0.8F * amp;
			rightLeg.xRot = Mth.cos(walk) * 0.8F * amp;
			float sway = Mth.cos(walk) * 0.6F * amp;
			leftArm.xRot = sway;
			rightArm.xRot = -sway;
			leftArm.zRot = -0.08F - Mth.sin(t * 0.08F) * 0.03F;
			rightArm.zRot = 0.08F + Mth.sin(t * 0.08F) * 0.03F;
			if (state.attack > 0) {  // размашистый удар: обе руки вверх и вниз
				float a = Mth.sin(state.attack * Mth.PI);
				leftArm.xRot = -2.4F * a;
				rightArm.xRot = -2.4F * a;
			}
			if (state.slam > 0) {  // сотрясение: поднять руки над головой и обрушить
				float p = 1.0F - state.slam;
				float lift = p < 0.6F ? p / 0.6F : 1.0F - (p - 0.6F) / 0.4F;
				leftArm.xRot = -3.0F * lift;
				rightArm.xRot = -3.0F * lift;
				leftArm.zRot = -0.3F * lift;
				rightArm.zRot = 0.3F * lift;
				body.xRot = p > 0.6F ? 0.35F * (1.0F - lift) : -0.15F * lift;
			} else {
				body.xRot = 0;
			}
			core.xScale = core.yScale = core.zScale = 1.0F + Mth.sin(t * 0.25F) * 0.08F;  // «сердце» пульсирует
			for (int i = 0; i < 4; i++) {  // пластины щита кружат вокруг стража
				ModelPart s = shards[i];
				s.visible = state.shield;
				float ang = t * 0.12F + i * Mth.HALF_PI;
				s.x = Mth.cos(ang) * 15;
				s.z = Mth.sin(ang) * 15;
				s.y = 0 + Mth.sin(t * 0.2F + i) * 2;
				s.yRot = -ang + Mth.HALF_PI;
			}
		}
	}

	// ---------------------------------------------------------------- Ледяной волк (128×64)
	public static class IceWolf extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart head;
		private final ModelPart tail;
		private final ModelPart frontLeft;
		private final ModelPart frontRight;
		private final ModelPart hindLeft;
		private final ModelPart hindRight;
		private final ModelPart saddle;
		private final ModelPart leftEar;
		private final ModelPart rightEar;

		public IceWolf(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.head = root.getChild("head");
			this.tail = body.getChild("tail");
			this.saddle = body.getChild("saddle");
			this.frontLeft = root.getChild("front_left");
			this.frontRight = root.getChild("front_right");
			this.hindLeft = root.getChild("hind_left");
			this.hindRight = root.getChild("hind_right");
			this.leftEar = head.getChild("left_ear");
			this.rightEar = head.getChild("right_ear");
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create()
					.texOffs(0, 0).addBox(-5, -5, -10, 10, 10, 20)
					.texOffs(0, 30).addBox(-6, -7, -12, 12, 12, 8),
				PartPose.offset(0, 11, 0));
			for (int i = 0; i < 4; i++) {  // гребень инея вдоль хребта
				body.addOrReplaceChild("crest" + i, CubeListBuilder.create().texOffs(110, 16).addBox(-0.5F, -3, -1, 1, 3, 2),
					PartPose.offsetAndRotation(0, -5, -5 + i * 4, -0.35F, 0, 0));
			}
			body.addOrReplaceChild("tail", CubeListBuilder.create().texOffs(80, 16).addBox(-1.5F, -1.5F, 0, 3, 3, 12),
				PartPose.offsetAndRotation(0, -3, 10, -0.6F, 0, 0));
			body.addOrReplaceChild("saddle", CubeListBuilder.create().texOffs(40, 50).addBox(-5.5F, -5.6F, -4, 11, 1, 9)
				.texOffs(80, 34).addBox(-5.6F, -5, -0.5F, 1, 10, 2).addBox(4.6F, -5, -0.5F, 1, 10, 2), PartPose.ZERO);
			PartDefinition head = root.addOrReplaceChild("head", CubeListBuilder.create().texOffs(64, 0).addBox(-4, -4, -7, 8, 8, 7)
				.texOffs(94, 0).addBox(-2, 0, -12, 4, 4, 5), PartPose.offset(0, 8, -12));
			head.addOrReplaceChild("left_ear", CubeListBuilder.create().texOffs(112, 0).addBox(-1, -4, 0, 2, 4, 1),
				PartPose.offsetAndRotation(2.5F, -4, -3, 0, 0, 0.15F));
			head.addOrReplaceChild("right_ear", CubeListBuilder.create().texOffs(112, 0).mirror().addBox(-1, -4, 0, 2, 4, 1),
				PartPose.offsetAndRotation(-2.5F, -4, -3, 0, 0, -0.15F));
			CubeListBuilder leg = CubeListBuilder.create().texOffs(64, 16).addBox(-2, 0, -2, 4, 12, 4);
			root.addOrReplaceChild("front_left", leg, PartPose.offset(3, 12, -7));
			root.addOrReplaceChild("front_right", CubeListBuilder.create().texOffs(64, 16).mirror().addBox(-2, 0, -2, 4, 12, 4), PartPose.offset(-3, 12, -7));
			root.addOrReplaceChild("hind_left", leg, PartPose.offset(3, 12, 8));
			root.addOrReplaceChild("hind_right", CubeListBuilder.create().texOffs(64, 16).mirror().addBox(-2, 0, -2, 4, 12, 4), PartPose.offset(-3, 12, 8));
			return LayerDefinition.create(mesh, 128, 64);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float speed = state.ridden ? 0.8F : 0.6662F;
			float walk = state.walkAnimationPos * speed;
			float amp = Math.min(1.0F, state.walkAnimationSpeed) * (state.ridden ? 1.25F : 1.0F);
			float t = state.ageInTicks;
			head.yRot = state.yRot * Mth.DEG_TO_RAD;
			head.xRot = state.xRot * Mth.DEG_TO_RAD + Mth.sin(walk) * 0.05F * amp;
			// галоп: передние и задние лапы парами, корпус покачивается
			frontLeft.xRot = Mth.cos(walk) * 1.1F * amp;
			frontRight.xRot = Mth.cos(walk + 0.4F) * 1.1F * amp;
			hindLeft.xRot = Mth.cos(walk + Mth.PI) * 1.1F * amp;
			hindRight.xRot = Mth.cos(walk + Mth.PI + 0.4F) * 1.1F * amp;
			body.xRot = Mth.sin(walk) * 0.06F * amp;
			tail.yRot = Mth.sin(t * 0.15F) * 0.25F + Mth.cos(walk) * 0.2F * amp;
			tail.xRot = -0.6F + amp * 0.35F;
			float twitch = Mth.sin(t * 0.07F) > 0.97F ? 0.3F : 0;  // изредка поводит ушами
			leftEar.zRot = 0.15F + twitch;
			rightEar.zRot = -0.15F - twitch;
			saddle.visible = state.saddled;
		}
	}
}
