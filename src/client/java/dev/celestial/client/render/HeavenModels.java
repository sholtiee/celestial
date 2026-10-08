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

/**
 * Свои модели существ Рая и Угасания (вместо перекрашенных ванильных): Тень, Грозовой дух/элементаль.
 * Развёртки совпадают с texOffs — текстуры рисует tools/gen_heaven_mobs.py.
 */
public final class HeavenModels {
	private HeavenModels() {}

	public static class State extends LivingEntityRenderState {
		public float attack;
		public int variant;
	}

	/** Нимб из четырёх светящихся планок над головой (у ангела и херувима); u — столбец развёртки: планки (u,0), бока (u,4). */
	static void halo(PartDefinition head, float y, float r, int u) {
		head.addOrReplaceChild("halo_front", CubeListBuilder.create().texOffs(u, 0).addBox(-r, 0, -0.5F, r * 2, 1, 1), PartPose.offset(0, y, -r));
		head.addOrReplaceChild("halo_back", CubeListBuilder.create().texOffs(u, 0).addBox(-r, 0, -0.5F, r * 2, 1, 1), PartPose.offset(0, y, r));
		head.addOrReplaceChild("halo_left", CubeListBuilder.create().texOffs(u, 4).addBox(-0.5F, 0, -r + 1, 1, 1, r * 2 - 2), PartPose.offset(r - 0.5F, y, 0));
		head.addOrReplaceChild("halo_right", CubeListBuilder.create().texOffs(u, 4).addBox(-0.5F, 0, -r + 1, 1, 1, r * 2 - 2), PartPose.offset(-r + 0.5F, y, 0));
	}

	// ---------------------------------------------------------------- Ангел (64×64): одеяние до земли, рукава, большие крылья, нимб
	public static class Angel extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart head;
		private final ModelPart skirt;
		private final ModelPart leftArm;
		private final ModelPart rightArm;
		private final ModelPart leftWing;
		private final ModelPart rightWing;

		public Angel(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.head = root.getChild("head");
			this.skirt = root.getChild("skirt");
			this.leftArm = body.getChild("left_arm");
			this.rightArm = body.getChild("right_arm");
			this.leftWing = body.getChild("left_wing");
			this.rightWing = body.getChild("right_wing");
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition head = root.addOrReplaceChild("head", CubeListBuilder.create().texOffs(0, 0).addBox(-4, -8, -4, 8, 8, 8), PartPose.offset(0, 0, 0));
			halo(head, -12, 4.5F, 32);
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(16, 16).addBox(-4, 0, -2, 8, 10, 4), PartPose.ZERO);
			body.addOrReplaceChild("left_arm", CubeListBuilder.create().texOffs(40, 16).addBox(-1, -1, -1.5F, 3, 11, 3), PartPose.offset(5, 1, 0));
			body.addOrReplaceChild("right_arm", CubeListBuilder.create().texOffs(40, 16).mirror().addBox(-2, -1, -1.5F, 3, 11, 3), PartPose.offset(-5, 1, 0));
			body.addOrReplaceChild("left_wing", CubeListBuilder.create().texOffs(32, 32).addBox(0, -2, 0, 1, 16, 10),
				PartPose.offsetAndRotation(1.5F, 1, 2, 0.25F, 0.5F, 0));
			body.addOrReplaceChild("right_wing", CubeListBuilder.create().texOffs(32, 32).mirror().addBox(-1, -2, 0, 1, 16, 10),
				PartPose.offsetAndRotation(-1.5F, 1, 2, 0.25F, -0.5F, 0));
			root.addOrReplaceChild("skirt", CubeListBuilder.create().texOffs(0, 32).addBox(-5, 0, -3, 10, 14, 6), PartPose.offset(0, 10, 0));
			return LayerDefinition.create(mesh, 64, 64);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float t = state.ageInTicks;
			float walk = state.walkAnimationPos * 0.6F;
			float amp = Math.min(1.0F, state.walkAnimationSpeed);
			head.yRot = state.yRot * Mth.DEG_TO_RAD;
			head.xRot = state.xRot * Mth.DEG_TO_RAD;
			leftArm.xRot = Mth.cos(walk) * 0.5F * amp + Mth.sin(t * 0.06F) * 0.05F;
			rightArm.xRot = -Mth.cos(walk) * 0.5F * amp - Mth.sin(t * 0.06F) * 0.05F;
			leftArm.zRot = -0.08F;
			rightArm.zRot = 0.08F;
			skirt.xRot = Mth.sin(walk) * 0.08F * amp;
			skirt.zRot = Mth.cos(walk) * 0.04F * amp;
			// крылья сложены и чуть подрагивают; на ходу приоткрываются
			float open = 0.5F + amp * 0.35F + Mth.sin(t * 0.08F) * 0.06F;
			leftWing.yRot = open;
			rightWing.yRot = -open;
			leftWing.zRot = -0.05F - amp * 0.1F;
			rightWing.zRot = 0.05F + amp * 0.1F;
		}
	}

	// ---------------------------------------------------------------- Херувим (64×32): большая голова, маленькое тельце, трепещущие крылышки, нимб
	public static class Cherub extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart head;
		private final ModelPart leftWing;
		private final ModelPart rightWing;
		private final ModelPart leftArm;
		private final ModelPart rightArm;

		public Cherub(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.head = body.getChild("head");
			this.leftWing = body.getChild("left_wing");
			this.rightWing = body.getChild("right_wing");
			this.leftArm = body.getChild("left_arm");
			this.rightArm = body.getChild("right_arm");
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(0, 16).addBox(-2, 0, -1.5F, 4, 5, 3), PartPose.offset(0, 16, 0));
			PartDefinition head = body.addOrReplaceChild("head", CubeListBuilder.create().texOffs(0, 0).addBox(-3, -6, -3, 6, 6, 6), PartPose.ZERO);
			halo(head, -9.5F, 3.5F, 48);
			body.addOrReplaceChild("left_arm", CubeListBuilder.create().texOffs(14, 16).addBox(0, 0, -1, 1, 4, 2), PartPose.offset(2, 0.5F, 0));
			body.addOrReplaceChild("right_arm", CubeListBuilder.create().texOffs(14, 16).mirror().addBox(-1, 0, -1, 1, 4, 2), PartPose.offset(-2, 0.5F, 0));
			body.addOrReplaceChild("left_wing", CubeListBuilder.create().texOffs(24, 0).addBox(0, -3, 0, 0, 6, 8), PartPose.offset(0.5F, 1, 1.5F));
			body.addOrReplaceChild("right_wing", CubeListBuilder.create().texOffs(24, 0).mirror().addBox(0, -3, 0, 0, 6, 8), PartPose.offset(-0.5F, 1, 1.5F));
			body.addOrReplaceChild("legs", CubeListBuilder.create().texOffs(20, 16).addBox(-1.5F, 5, -1, 3, 2, 2), PartPose.ZERO);
			return LayerDefinition.create(mesh, 64, 32);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float t = state.ageInTicks;
			body.y = 16 + Mth.sin(t * 0.15F) * 1.0F;  // парит
			head.yRot = state.yRot * Mth.DEG_TO_RAD;
			head.xRot = state.xRot * Mth.DEG_TO_RAD;
			float flap = Mth.sin(t * 1.4F) * 0.6F;  // часто-часто машет крылышками
			leftWing.yRot = 0.6F + flap;
			rightWing.yRot = -0.6F - flap;
			leftArm.zRot = -0.3F - Mth.sin(t * 0.2F) * 0.15F;
			rightArm.zRot = 0.3F + Mth.sin(t * 0.2F) * 0.15F;
			body.xRot = 0.1F + Math.min(1.0F, state.walkAnimationSpeed) * 0.4F;
		}
	}

	// ---------------------------------------------------------------- Тень (64×64): капюшон, длинные когтистые руки, хвосты дыма вместо ног
	public static class Shadow extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart head;
		private final ModelPart leftArm;
		private final ModelPart rightArm;
		private final ModelPart[] tails = new ModelPart[3];
		private final ModelPart cloakLeft;
		private final ModelPart cloakRight;

		public Shadow(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.head = body.getChild("head");
			this.leftArm = body.getChild("left_arm");
			this.rightArm = body.getChild("right_arm");
			this.cloakLeft = body.getChild("cloak_left");
			this.cloakRight = body.getChild("cloak_right");
			for (int i = 0; i < 3; i++) {
				tails[i] = body.getChild("tail" + i);
			}
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(0, 16).addBox(-4, -12, -2.5F, 8, 12, 5)
				.texOffs(26, 16).addBox(-3, 0, -2, 6, 3, 4), PartPose.offset(0, 9, 0));
			body.addOrReplaceChild("head", CubeListBuilder.create().texOffs(0, 0).addBox(-4, -8, -4, 8, 8, 8)
				.texOffs(0, 48).addBox(-4.5F, -9, -4.5F, 9, 4, 9), PartPose.offset(0, -12, 0));
			body.addOrReplaceChild("left_arm", CubeListBuilder.create().texOffs(48, 16).addBox(-1, -1, -1.5F, 3, 15, 3)
				.texOffs(26, 24).addBox(-1, 14, -2.5F, 3, 3, 1), PartPose.offset(5, -11, 0));
			body.addOrReplaceChild("right_arm", CubeListBuilder.create().texOffs(48, 16).mirror().addBox(-2, -1, -1.5F, 3, 15, 3)
				.texOffs(26, 24).addBox(-2, 14, -2.5F, 3, 3, 1), PartPose.offset(-5, -11, 0));
			body.addOrReplaceChild("cloak_left", CubeListBuilder.create().texOffs(40, 34).addBox(0, 0, 0, 4, 16, 1), PartPose.offset(0, -12, 2.6F));
			body.addOrReplaceChild("cloak_right", CubeListBuilder.create().texOffs(40, 34).mirror().addBox(-4, 0, 0, 4, 16, 1), PartPose.offset(0, -12, 2.6F));
			int[][] t = {{-2, 0}, {2, 0}, {0, 1}};
			for (int i = 0; i < 3; i++) {
				PartDefinition tail = body.addOrReplaceChild("tail" + i, CubeListBuilder.create().texOffs(12, 34).addBox(-1.5F, 0, -1.5F, 3, 6, 3),
					PartPose.offset(t[i][0], 3, t[i][1]));
				tail.addOrReplaceChild("tip", CubeListBuilder.create().texOffs(24, 34).addBox(-1, 0, -1, 2, 6, 2), PartPose.offset(0, 6, 0));
			}
			return LayerDefinition.create(mesh, 64, 64);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float t = state.ageInTicks;
			float walk = state.walkAnimationPos * 0.5F;
			float amp = Math.min(1.0F, state.walkAnimationSpeed);
			body.y = 9 + Mth.sin(t * 0.09F) * 1.0F;  // парит над землёй
			body.xRot = 0.15F + amp * 0.25F;  // на бегу клонится вперёд
			head.yRot = state.yRot * Mth.DEG_TO_RAD;
			head.xRot = state.xRot * Mth.DEG_TO_RAD - body.xRot;
			float reach = state.attack > 0 ? -1.6F * Mth.sin(state.attack * Mth.PI) : 0;
			leftArm.xRot = -0.3F + Mth.cos(walk) * 0.6F * amp + Mth.sin(t * 0.07F) * 0.08F + reach;
			rightArm.xRot = -0.3F - Mth.cos(walk) * 0.6F * amp - Mth.sin(t * 0.07F) * 0.08F + reach;
			leftArm.zRot = -0.12F;
			rightArm.zRot = 0.12F;
			for (int i = 0; i < 3; i++) {  // хвосты дыма извиваются
				tails[i].xRot = 0.25F + Mth.sin(t * 0.15F + i * 2.1F) * 0.35F + amp * 0.4F;
				tails[i].zRot = Mth.cos(t * 0.12F + i) * 0.2F;
				tails[i].getChild("tip").xRot = Mth.sin(t * 0.2F + i) * 0.4F;
			}
			cloakLeft.xRot = 0.15F + amp * 0.6F + Mth.sin(t * 0.11F) * 0.08F;
			cloakRight.xRot = 0.15F + amp * 0.6F + Mth.sin(t * 0.11F + 1) * 0.08F;
		}
	}

	// ---------------------------------------------------------------- Грозовой дух (64×64): ядро-шар грозы, кольца облаков, ломаные молнии вокруг
	public static class Storm extends EntityModel<State> {
		private final ModelPart core;
		private final ModelPart[] puffs = new ModelPart[8];
		private final ModelPart[] bolts = new ModelPart[6];

		public Storm(ModelPart root) {
			super(root);
			this.core = root.getChild("core");
			for (int i = 0; i < puffs.length; i++) {
				puffs[i] = root.getChild("puff" + i);
			}
			for (int i = 0; i < bolts.length; i++) {
				bolts[i] = root.getChild("bolt" + i);
			}
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition core = root.addOrReplaceChild("core", CubeListBuilder.create().texOffs(0, 0).addBox(-4, -4, -4, 8, 8, 8),
				PartPose.offset(0, 6, 0));
			core.addOrReplaceChild("eyes", CubeListBuilder.create().texOffs(32, 0).addBox(-3, -1.5F, -4.6F, 6, 2, 1), PartPose.ZERO);
			for (int i = 0; i < 8; i++) {
				int w = i % 2 == 0 ? 8 : 7;
				root.addOrReplaceChild("puff" + i, CubeListBuilder.create().texOffs(0, 16 + (i % 2) * 14).addBox(-w / 2.0F, -w / 2.0F + 2, -w / 2.0F, w, w - 2, w),
					PartPose.ZERO);
			}
			for (int i = 0; i < 6; i++) {  // молния — три коротких колена под углами
				PartDefinition bolt = root.addOrReplaceChild("bolt" + i, CubeListBuilder.create().texOffs(48, 0).addBox(-0.5F, -4, -0.5F, 1, 4, 1),
					PartPose.ZERO);
				PartDefinition mid = bolt.addOrReplaceChild("mid", CubeListBuilder.create().texOffs(52, 0).addBox(-0.5F, 0, -0.5F, 1, 4, 1),
					PartPose.rotation(0, 0, 0.6F));
				mid.addOrReplaceChild("end", CubeListBuilder.create().texOffs(56, 0).addBox(-0.5F, 0, -0.5F, 1, 4, 1),
					PartPose.offsetAndRotation(0, 4, 0, 0, 0, -1.1F));
			}
			return LayerDefinition.create(mesh, 64, 64);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float t = state.ageInTicks;
			core.y = 6 + Mth.sin(t * 0.1F) * 1.2F;
			core.yRot = state.yRot * Mth.DEG_TO_RAD;
			core.xScale = core.yScale = core.zScale = 1.0F + Mth.sin(t * 0.6F) * 0.05F;  // пульс грозы
			for (int i = 0; i < puffs.length; i++) {  // два кольца облаков, вращаются навстречу
				boolean upper = i < 4;
				float a = (upper ? t * 0.06F : -t * 0.05F) + (i % 4) * Mth.HALF_PI + (upper ? 0 : Mth.PI / 4);
				float r = upper ? 7.5F : 9F;
				puffs[i].x = Mth.cos(a) * r;
				puffs[i].z = Mth.sin(a) * r;
				puffs[i].y = (upper ? 1 : 10) + Mth.sin(t * 0.08F + i) * 0.8F;
				puffs[i].yRot = -a;
			}
			for (int i = 0; i < bolts.length; i++) {  // молнии вспыхивают и меняют угол рывками
				ModelPart b = bolts[i];
				int phase = (int) (t / 3 + i * 7) % 11;
				b.visible = phase < 6;
				float a = i * Mth.TWO_PI / bolts.length + t * 0.03F;
				b.x = Mth.cos(a) * 9;
				b.z = Mth.sin(a) * 9;
				b.y = 9 + (phase % 3);
				b.zRot = (phase % 2 == 0 ? 0.4F : -0.4F);
				b.yRot = -a;
			}
		}
	}
}
