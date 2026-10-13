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

/** Модели существ Астрала. Развёртки совпадают с texOffs (рисует tools/gen_astral_mobs.py). */
public final class AstralModels {
	private AstralModels() {}

	public static class State extends LivingEntityRenderState {
		public float bite;
	}

	// ---------------------------------------------------------------- Звёздная рыба (32×32)
	public static class Fish extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart tail;
		private final ModelPart leftFin;
		private final ModelPart rightFin;

		public Fish(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.tail = body.getChild("tail");
			this.leftFin = body.getChild("left_fin");
			this.rightFin = body.getChild("right_fin");
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(0, 0).addBox(-1.5F, -2, -3, 3, 4, 6)
				.texOffs(18, 0).addBox(0, -4, -1, 0, 2, 3), PartPose.offset(0, 21, 0));
			body.addOrReplaceChild("tail", CubeListBuilder.create().texOffs(0, 10).addBox(0, -2.5F, 0, 0, 5, 4), PartPose.offset(0, 0, 3));
			body.addOrReplaceChild("left_fin", CubeListBuilder.create().texOffs(10, 10).addBox(0, 0, -1, 3, 0, 2), PartPose.offsetAndRotation(1.5F, 1, 0, 0, 0, 0.5F));
			body.addOrReplaceChild("right_fin", CubeListBuilder.create().texOffs(10, 10).mirror().addBox(-3, 0, -1, 3, 0, 2), PartPose.offsetAndRotation(-1.5F, 1, 0, 0, 0, -0.5F));
			return LayerDefinition.create(mesh, 32, 32);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float t = state.ageInTicks;
			tail.yRot = Mth.sin(t * 0.6F) * 0.5F;
			body.yRot = Mth.sin(t * 0.6F + 1) * 0.08F;
			leftFin.zRot = 0.5F + Mth.sin(t * 0.4F) * 0.3F;
			rightFin.zRot = -leftFin.zRot;
			body.xRot = state.xRot * Mth.DEG_TO_RAD;
		}
	}

	// ---------------------------------------------------------------- Пожиратель звёзд (64×64)
	public static class Devourer extends EntityModel<State> {
		static final int SEGS = 6;
		private final ModelPart head;
		private final ModelPart jaw;
		private final ModelPart[] segs = new ModelPart[SEGS];

		public Devourer(ModelPart root) {
			super(root);
			this.head = root.getChild("head");
			this.jaw = head.getChild("jaw");
			ModelPart p = head;
			for (int i = 0; i < SEGS; i++) {
				p = p.getChild("seg" + i);
				segs[i] = p;
			}
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition head = root.addOrReplaceChild("head", CubeListBuilder.create().texOffs(0, 0).addBox(-4, -4, -7, 8, 5, 7),
				PartPose.offset(0, 18, -6));
			head.addOrReplaceChild("jaw", CubeListBuilder.create().texOffs(0, 12).addBox(-3.5F, 0, -6.5F, 7, 2, 7), PartPose.offset(0, 1, 0));
			// усы-щупы пасти
			head.addOrReplaceChild("whiskers", CubeListBuilder.create().texOffs(30, 0).addBox(-5, -1, -8, 1, 1, 5).addBox(4, -1, -8, 1, 1, 5),
				PartPose.ZERO);
			PartDefinition p = head;
			float z = 0;
			for (int i = 0; i < SEGS; i++) {
				float w = 7 - i, h = 5 - i * 0.6F;
				p = p.addOrReplaceChild("seg" + i, CubeListBuilder.create().texOffs(0, 22 + (i % 3) * 10).addBox(-w / 2, -h / 2 - 1, 0, w, h, 6),
					PartPose.offset(0, 0, z));
				z = 5.5F;
			}
			p.addOrReplaceChild("fin", CubeListBuilder.create().texOffs(30, 8).addBox(0, -4, 0, 0, 8, 6), PartPose.offset(0, -1, 5));
			return LayerDefinition.create(mesh, 64, 64);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float t = state.ageInTicks;
			head.yRot = state.yRot * Mth.DEG_TO_RAD * 0.5F;
			head.xRot = state.xRot * Mth.DEG_TO_RAD;
			for (int i = 0; i < SEGS; i++) {  // волна по телу
				segs[i].yRot = Mth.sin(t * 0.25F - i * 0.8F) * 0.35F;
				segs[i].xRot = Mth.cos(t * 0.18F - i * 0.6F) * 0.08F;
			}
			jaw.xRot = 0.15F + Mth.sin(t * 0.1F) * 0.05F + state.bite * 0.9F * Mth.sin(state.bite * Mth.PI);
		}
	}
}
