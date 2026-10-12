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

/** Модели существ Хронограда. Развёртки текстур совпадают с texOffs (рисует tools/gen_chrono_mobs.py). */
public final class ChronoModels {
	private ChronoModels() {}

	public static class State extends LivingEntityRenderState {
		public float attack;
		/** Заводится / подзаведён / завод есть (у каждого существа своё). */
		public boolean wound;
		public float rewind;
		public float beam;
		public boolean saddled;
		public boolean ridden;
	}

	/** Строевой шаг: нога «отбивается» резко и держится — синус, сжатый к ±1. */
	static float march(float x) {
		float s = Mth.sin(x);
		return Math.signum(s) * (float) Math.sqrt(Math.abs(s));
	}

	// ---------------------------------------------------------------- Часовой-механоид (64×64)
	public static class Sentry extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart head;
		private final ModelPart key;
		private final ModelPart leftArm;
		private final ModelPart rightArm;
		private final ModelPart leftLeg;
		private final ModelPart rightLeg;

		public Sentry(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.head = body.getChild("head");
			this.key = body.getChild("key");
			this.leftArm = body.getChild("left_arm");
			this.rightArm = body.getChild("right_arm");
			this.leftLeg = root.getChild("left_leg");
			this.rightLeg = root.getChild("right_leg");
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(0, 0).addBox(-5, 0, -3, 10, 12, 6),
				PartPose.offset(0, -1, 0));
			body.addOrReplaceChild("epaulettes", CubeListBuilder.create().texOffs(32, 32).addBox(-7, -1, -2.5F, 4, 2, 5)
				.texOffs(32, 32).mirror().addBox(3, -1, -2.5F, 4, 2, 5), PartPose.ZERO);
			PartDefinition head = body.addOrReplaceChild("head", CubeListBuilder.create().texOffs(0, 18).addBox(-3.5F, -7, -3.5F, 7, 7, 7)
				.texOffs(28, 18).addBox(-3, -11, -3, 6, 4, 6), PartPose.offset(0, 0, 0));
			head.addOrReplaceChild("lens", CubeListBuilder.create().texOffs(52, 18).addBox(-1.5F, -5, -4, 3, 3, 1), PartPose.ZERO);
			PartDefinition key = body.addOrReplaceChild("key", CubeListBuilder.create().texOffs(46, 0).addBox(-0.5F, -0.5F, 0, 1, 1, 2),
				PartPose.offset(0, 5, 3));
			key.addOrReplaceChild("bow", CubeListBuilder.create().texOffs(46, 4).addBox(-2.5F, -1, 2, 5, 2, 1), PartPose.ZERO);
			body.addOrReplaceChild("left_arm", CubeListBuilder.create().texOffs(32, 0).mirror().addBox(0, -1, -2, 3, 12, 4),
				PartPose.offset(5, 1, 0));
			PartDefinition right = body.addOrReplaceChild("right_arm", CubeListBuilder.create().texOffs(32, 0).addBox(-3, -1, -2, 3, 12, 4),
				PartPose.offset(-5, 1, 0));
			// алебарда: древко вдоль руки, лезвие наверху
			right.addOrReplaceChild("halberd", CubeListBuilder.create().texOffs(16, 32).addBox(-0.5F, -16, -0.5F, 1, 22, 1)
				.texOffs(20, 32).addBox(-0.5F, -16, -5, 1, 6, 5), PartPose.offsetAndRotation(-1.5F, 10, -1, 0, 0, 0));
			root.addOrReplaceChild("left_leg", CubeListBuilder.create().texOffs(0, 32).mirror().addBox(-2, 0, -2, 4, 13, 4), PartPose.offset(2.5F, 11, 0));
			root.addOrReplaceChild("right_leg", CubeListBuilder.create().texOffs(0, 32).addBox(-2, 0, -2, 4, 13, 4), PartPose.offset(-2.5F, 11, 0));
			return LayerDefinition.create(mesh, 64, 64);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float walk = state.walkAnimationPos * 0.6F;
			float amp = Math.min(1.0F, state.walkAnimationSpeed);
			float t = state.ageInTicks;
			head.yRot = state.yRot * Mth.DEG_TO_RAD;
			head.xRot = state.xRot * Mth.DEG_TO_RAD;
			float step = march(walk) * amp;
			leftLeg.xRot = -step * 0.9F;
			rightLeg.xRot = step * 0.9F;
			leftArm.xRot = step * 0.7F;
			rightArm.xRot = -0.35F;  // алебарда «на плечо»
			leftArm.zRot = -0.05F;
			rightArm.zRot = 0.05F;
			body.y = -1 + Math.abs(Mth.cos(walk)) * amp * 0.8F;
			body.xRot = 0;
			key.zRot = t * 0.08F;
			if (state.attack > 0) {  // рубящий удар алебардой сверху
				float a = Mth.sin(state.attack * Mth.PI);
				rightArm.xRot = -0.35F - 2.4F * a;
				body.xRot = 0.15F * a;
			}
			if (state.rewind > 0) {  // завод: обмяк, голова повисла, ключ крутится быстро
				float s = Math.min(1.0F, state.rewind * 4);
				body.xRot = 0.35F * s;
				head.xRot = 0.6F * s;
				leftArm.xRot = 0.2F * s;
				rightArm.xRot = -0.35F + 0.4F * s;
				leftArm.zRot = -0.2F * s;
				rightArm.zRot = 0.2F * s;
				key.zRot = t * 0.6F;
			}
		}
	}

	// ---------------------------------------------------------------- Жук-заводняк (64×32)
	public static class Beetle extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart key;
		private final ModelPart head;
		private final ModelPart[] legs = new ModelPart[6];

		public Beetle(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.key = body.getChild("key");
			this.head = body.getChild("head");
			for (int i = 0; i < 6; i++) {
				legs[i] = root.getChild("leg" + i);
			}
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(0, 0).addBox(-3, -4, -4, 6, 4, 8),
				PartPose.offset(0, 22, 0));
			PartDefinition head = body.addOrReplaceChild("head", CubeListBuilder.create().texOffs(0, 12).addBox(-2, -2, -3, 4, 3, 3),
				PartPose.offset(0, -1, -4));
			head.addOrReplaceChild("mandibles", CubeListBuilder.create().texOffs(14, 12).addBox(-2, 0, -2, 1, 1, 2)
				.texOffs(14, 12).mirror().addBox(1, 0, -2, 1, 1, 2), PartPose.offset(0, 0, -3));
			PartDefinition key = body.addOrReplaceChild("key", CubeListBuilder.create().texOffs(28, 4).addBox(-0.5F, -2, -0.5F, 1, 2, 1),
				PartPose.offset(0, -4, 1));
			key.addOrReplaceChild("bow", CubeListBuilder.create().texOffs(28, 8).addBox(-2, -4, -0.5F, 4, 2, 1), PartPose.ZERO);
			for (int i = 0; i < 6; i++) {
				boolean left = i % 2 == 0;
				float z = -2.5F + (i / 2) * 2.5F;
				CubeListBuilder leg = CubeListBuilder.create().texOffs(28, 0);
				if (left) {
					leg.addBox(0, -0.5F, -0.5F, 4, 1, 1);
				} else {
					leg.mirror().addBox(-4, -0.5F, -0.5F, 4, 1, 1);
				}
				root.addOrReplaceChild("leg" + i, leg, PartPose.offsetAndRotation(left ? 3 : -3, 21.5F, z, 0, 0, left ? 0.5F : -0.5F));
			}
			return LayerDefinition.create(mesh, 64, 32);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float speed = state.wound ? 1.6F : 1.0F;
			float walk = state.walkAnimationPos * 1.4F * speed;
			float amp = Math.min(1.0F, state.walkAnimationSpeed);
			float t = state.ageInTicks;
			for (int i = 0; i < 6; i++) {
				boolean left = i % 2 == 0;
				float phase = (i / 2 + (left ? 0 : 1)) % 2 == 0 ? 0 : Mth.PI;  // треножная походка
				legs[i].yRot = Mth.cos(walk + phase) * 0.45F * amp * (left ? 1 : -1);
				legs[i].zRot = (left ? 0.5F : -0.5F) + Math.max(0, Mth.sin(walk + phase)) * 0.4F * amp * (left ? -1 : 1);
			}
			head.yRot = state.yRot * Mth.DEG_TO_RAD * 0.5F;
			body.zRot = Mth.sin(walk) * 0.04F * amp;
			key.yRot = t * (state.wound ? 0.7F : 0.12F);
			if (state.attack > 0) {
				head.xRot = -0.4F * Mth.sin(state.attack * Mth.PI);
			} else {
				head.xRot = 0;
			}
		}
	}

	// ---------------------------------------------------------------- Кукла-латунь (64×64)
	public static class Doll extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart head;
		private final ModelPart key;
		private final ModelPart leftArm;
		private final ModelPart rightArm;
		private final ModelPart leftLeg;
		private final ModelPart rightLeg;

		public Doll(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.head = root.getChild("head");
			this.key = body.getChild("key");
			this.leftArm = root.getChild("left_arm");
			this.rightArm = root.getChild("right_arm");
			this.leftLeg = root.getChild("left_leg");
			this.rightLeg = root.getChild("right_leg");
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition head = root.addOrReplaceChild("head", CubeListBuilder.create().texOffs(0, 0).addBox(-4, -8, -4, 8, 8, 8),
				PartPose.offset(0, 2, 0));
			head.addOrReplaceChild("bonnet", CubeListBuilder.create().texOffs(0, 32).addBox(-4.5F, -8.6F, -3, 9, 3, 9), PartPose.ZERO);
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(0, 16).addBox(-4, 0, -2, 8, 12, 4)
				.texOffs(24, 16).addBox(-5, 8, -3, 10, 5, 6), PartPose.offset(0, 2, 0));
			PartDefinition key = body.addOrReplaceChild("key", CubeListBuilder.create().texOffs(56, 0).addBox(-0.5F, -0.5F, 0, 1, 1, 2),
				PartPose.offset(0, 4, 2));
			key.addOrReplaceChild("bow", CubeListBuilder.create().texOffs(56, 4).addBox(-1.5F, -1, 2, 3, 2, 1), PartPose.ZERO);
			root.addOrReplaceChild("left_arm", CubeListBuilder.create().texOffs(32, 0).mirror().addBox(-0.5F, -1, -1.5F, 3, 12, 3),
				PartPose.offset(4.5F, 3, 0));
			root.addOrReplaceChild("right_arm", CubeListBuilder.create().texOffs(32, 0).addBox(-2.5F, -1, -1.5F, 3, 12, 3),
				PartPose.offset(-4.5F, 3, 0));
			root.addOrReplaceChild("left_leg", CubeListBuilder.create().texOffs(44, 0).mirror().addBox(-1.5F, 0, -1.5F, 3, 10, 3),
				PartPose.offset(2, 14, 0));
			root.addOrReplaceChild("right_leg", CubeListBuilder.create().texOffs(44, 0).addBox(-1.5F, 0, -1.5F, 3, 10, 3),
				PartPose.offset(-2, 14, 0));
			return LayerDefinition.create(mesh, 64, 64);
		}

		/** Кукольная дёрганость: угол округляется до 1/6 рад — суставы «щёлкают». */
		private static float tick(float a) {
			return Math.round(a * 6) / 6.0F;
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float walk = state.walkAnimationPos * 0.66F;
			float amp = Math.min(1.0F, state.walkAnimationSpeed);
			float t = state.ageInTicks;
			head.yRot = tick(state.yRot * Mth.DEG_TO_RAD);
			head.xRot = tick(state.xRot * Mth.DEG_TO_RAD);
			head.zRot = tick(Mth.sin(t * 0.05F) * 0.25F);  // склоняет голову набок
			leftLeg.xRot = tick(Mth.cos(walk) * 1.0F * amp);
			rightLeg.xRot = tick(-Mth.cos(walk) * 1.0F * amp);
			leftArm.xRot = tick(-Mth.cos(walk) * 0.8F * amp);
			rightArm.xRot = tick(Mth.cos(walk) * 0.8F * amp);
			leftArm.zRot = -0.12F;
			rightArm.zRot = 0.12F;
			key.zRot = t * 0.15F;
			if (state.attack > 0) {  // обе руки вперёд — хватает
				float a = Mth.sin(state.attack * Mth.PI);
				leftArm.xRot = tick(-1.5F * a);
				rightArm.xRot = tick(-1.5F * a);
			}
		}
	}

	// ---------------------------------------------------------------- Офаним (64×64)
	public static class Ophanim extends EntityModel<State> {
		static final int SEGMENTS = 12;
		private final ModelPart eye;
		private final ModelPart ringA;
		private final ModelPart ringB;
		private final ModelPart ringC;
		private final ModelPart holdB;
		private final ModelPart holdC;

		public Ophanim(ModelPart root) {
			super(root);
			ModelPart wheels = root.getChild("wheels");
			this.eye = wheels.getChild("eye");
			this.ringA = wheels.getChild("ring_a");
			this.holdB = wheels.getChild("hold_b");
			this.holdC = wheels.getChild("hold_c");
			this.ringB = holdB.getChild("ring_b");
			this.ringC = holdC.getChild("ring_c");
		}

		/** Кольцо в плоскости XY из сегментов, каждое третье несёт око (торчит в обе стороны кольца). */
		private static void ring(PartDefinition parent, float radius, int texV) {
			for (int i = 0; i < SEGMENTS; i++) {
				float a = i * Mth.TWO_PI / SEGMENTS;
				float len = radius * Mth.TWO_PI / SEGMENTS + 0.6F;
				CubeListBuilder seg = CubeListBuilder.create().texOffs(0, texV).addBox(-len / 2, -1, -1, len, 2, 2);
				if (i % 3 == 0) {
					seg.texOffs(32, 0).addBox(-1, -1.5F, -1.5F, 2, 3, 3);
				}
				parent.addOrReplaceChild("s" + i, seg, PartPose.offsetAndRotation(Mth.cos(a) * radius, Mth.sin(a) * radius, 0, 0, 0, a + Mth.HALF_PI));
			}
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition wheels = root.addOrReplaceChild("wheels", CubeListBuilder.create(), PartPose.offset(0, 10, 0));
			wheels.addOrReplaceChild("eye", CubeListBuilder.create().texOffs(0, 0).addBox(-4, -4, -4, 8, 8, 8), PartPose.ZERO);
			ring(wheels.addOrReplaceChild("ring_a", CubeListBuilder.create(), PartPose.ZERO), 11, 16);
			ring(wheels.addOrReplaceChild("hold_b", CubeListBuilder.create(), PartPose.rotation(0, Mth.HALF_PI, 0))
				.addOrReplaceChild("ring_b", CubeListBuilder.create(), PartPose.ZERO), 9, 20);
			ring(wheels.addOrReplaceChild("hold_c", CubeListBuilder.create(), PartPose.rotation(Mth.HALF_PI, 0, 0))
				.addOrReplaceChild("ring_c", CubeListBuilder.create(), PartPose.ZERO), 6, 24);
			return LayerDefinition.create(mesh, 64, 64);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float t = state.ageInTicks;
			float speed = 1.0F + state.beam * 3.0F;  // при наводке колёса раскручиваются
			ringA.zRot = t * 0.04F * speed;
			ringB.zRot = -t * 0.05F * speed;
			ringC.zRot = t * 0.07F * speed;
			// внутренние колёса кувыркаются — «колесо в колесе» (Иез. 1:16) видно с любой стороны
			holdB.yRot = Mth.HALF_PI + t * 0.021F * speed;
			holdB.xRot = 0.5F;
			holdC.xRot = Mth.HALF_PI + t * 0.017F * speed;
			holdC.zRot = 0.6F;
			eye.yRot = state.yRot * Mth.DEG_TO_RAD;
			eye.xRot = state.xRot * Mth.DEG_TO_RAD;
			float pulse = 1.0F + state.beam * 0.25F + Mth.sin(t * 0.2F) * 0.04F;
			eye.xScale = eye.yScale = eye.zScale = pulse;
			root().y = Mth.sin(t * 0.08F) * 1.2F;  // покачивается в воздухе
		}
	}

	// ---------------------------------------------------------------- Заводной конь (128×64)
	public static class Horse extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart neck;
		private final ModelPart head;
		private final ModelPart tail;
		private final ModelPart key;
		private final ModelPart saddle;
		private final ModelPart[] legs = new ModelPart[4];

		public Horse(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.neck = root.getChild("neck");
			this.head = neck.getChild("head");
			this.tail = body.getChild("tail");
			this.key = body.getChild("key");
			this.saddle = body.getChild("saddle");
			String[] names = {"front_left", "front_right", "hind_left", "hind_right"};
			for (int i = 0; i < 4; i++) {
				legs[i] = root.getChild(names[i]);
			}
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(0, 0).addBox(-5, -5, -11, 10, 10, 22),
				PartPose.offset(0, 5, 0));
			body.addOrReplaceChild("stack", CubeListBuilder.create().texOffs(0, 32).addBox(-1.5F, -6, -1.5F, 3, 6, 3), PartPose.offset(0, -5, 7));
			body.addOrReplaceChild("tail", CubeListBuilder.create().texOffs(110, 16).addBox(-0.5F, -0.5F, 0, 1, 1, 8),
				PartPose.offsetAndRotation(0, -3, 11, -0.7F, 0, 0));
			PartDefinition key = body.addOrReplaceChild("key", CubeListBuilder.create().texOffs(100, 16).addBox(0, -0.5F, -0.5F, 3, 1, 1),
				PartPose.offset(5, -1, 2));
			key.addOrReplaceChild("bow", CubeListBuilder.create().texOffs(100, 20).addBox(3, -2, -2, 1, 4, 4), PartPose.ZERO);
			body.addOrReplaceChild("saddle", CubeListBuilder.create().texOffs(12, 32).addBox(-5.5F, -5.6F, -6, 11, 1, 10)
				.texOffs(54, 32).addBox(-6, -5, -1.5F, 1, 8, 2).addBox(5, -5, -1.5F, 1, 8, 2), PartPose.ZERO);
			PartDefinition neck = root.addOrReplaceChild("neck", CubeListBuilder.create().texOffs(64, 0).addBox(-2.5F, -7, -2.5F, 5, 7, 5),
				PartPose.offsetAndRotation(0, 2, -9, 0.8F, 0, 0));
			PartDefinition head = neck.addOrReplaceChild("head", CubeListBuilder.create().texOffs(84, 0).addBox(-3, -5, -9, 6, 5, 9),
				PartPose.offsetAndRotation(0, -6, 1, -0.8F, 0, 0));
			head.addOrReplaceChild("ears", CubeListBuilder.create().texOffs(114, 0).addBox(-2.5F, -8, -1, 1, 3, 1)
				.texOffs(114, 0).mirror().addBox(1.5F, -8, -1, 1, 3, 1), PartPose.ZERO);
			String[] names = {"front_left", "front_right", "hind_left", "hind_right"};
			for (int i = 0; i < 4; i++) {
				boolean left = i % 2 == 0;
				CubeListBuilder leg = CubeListBuilder.create().texOffs(64, 16);
				if (!left) {
					leg.mirror();
				}
				leg.addBox(-1.5F, 0, -1.5F, 3, 7, 3).texOffs(76, 16).addBox(-1, 7, -1, 2, 5, 2).texOffs(84, 16).addBox(-2, 12, -2, 4, 2, 4);
				root.addOrReplaceChild(names[i], leg, PartPose.offset(left ? 3.5F : -3.5F, 10, i < 2 ? -8 : 8));
			}
			return LayerDefinition.create(mesh, 128, 64);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float walk = state.walkAnimationPos * (state.ridden ? 0.8F : 0.6662F);
			float amp = Math.min(1.0F, state.walkAnimationSpeed) * (state.ridden ? 1.2F : 1.0F);
			float t = state.ageInTicks;
			// рысь: диагональные пары, движение ровное, как у шатунов
			legs[0].xRot = Mth.cos(walk) * 0.9F * amp;
			legs[3].xRot = Mth.cos(walk) * 0.9F * amp;
			legs[1].xRot = Mth.cos(walk + Mth.PI) * 0.9F * amp;
			legs[2].xRot = Mth.cos(walk + Mth.PI) * 0.9F * amp;
			neck.xRot = 0.8F + Mth.sin(walk * 2) * 0.04F * amp + (state.wound ? 0 : 0.45F);  // без завода голова опущена
			neck.yRot = state.yRot * Mth.DEG_TO_RAD * 0.6F;
			head.xRot = -0.8F + state.xRot * Mth.DEG_TO_RAD * 0.5F;
			tail.yRot = state.wound ? Mth.sin(t * 0.3F) * 0.2F : 0;
			tail.xRot = state.wound ? -0.7F + amp * 0.3F : -0.2F;
			key.xRot = state.wound ? t * (state.ridden ? 0.4F : 0.1F) : 0;
			body.y = 5 + Math.abs(Mth.sin(walk)) * amp * 0.6F;
			saddle.visible = state.saddled;
		}
	}
}
