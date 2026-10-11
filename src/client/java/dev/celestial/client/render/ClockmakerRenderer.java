package dev.celestial.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.celestial.Celestial;
import dev.celestial.boss.Clockmaker;
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
 * Часовщик-Механоид: латунный механический ангел на колесе-престоле офаним («колесо в колесе», ободья полны очей, Иез. 1:16–18).
 * Вместо лица — циферблат со стрелками, за головой вращается шестерня-нимб, четыре руки кончаются клинками-стрелками,
 * под корпусом качается маятник. Взмах — корпус проворачивается полным оборотом, как стрелка; перед «Стой!» стрелки замирают на полуночи.
 */
public final class ClockmakerRenderer {
	public static final ModelLayerLocation LAYER = new ModelLayerLocation(Celestial.id("clockmaker"), "main");
	private static final int SEGMENTS = 16;
	private static final float WHEEL_R = 13.0F;

	private ClockmakerRenderer() {}

	public static void init() {
		ModelLayerRegistry.registerModelLayer(LAYER, Model::createLayer);
		EntityRendererRegistry.register(ModEntities.CLOCKMAKER, Boss::new);
		EntityRendererRegistry.register(ModEntities.CLOCK_GEAR, ctx -> new ThrownItemRenderer<>(ctx, 1.6F, true));
	}

	public static class State extends LivingEntityRenderState {
		public int phase;
		public float sweep;
		public boolean warning;
	}

	public static class Model extends EntityModel<State> {
		private final ModelPart body;
		private final ModelPart head;
		private final ModelPart hourHand;
		private final ModelPart minuteHand;
		private final ModelPart halo;
		private final ModelPart[] arms = new ModelPart[4];
		private final ModelPart pendulum;
		private final ModelPart ringA;
		private final ModelPart ringB;

		public Model(ModelPart root) {
			super(root);
			this.body = root.getChild("body");
			this.head = body.getChild("head");
			this.hourHand = head.getChild("hour_hand");
			this.minuteHand = head.getChild("minute_hand");
			this.halo = head.getChild("halo");
			for (int i = 0; i < 4; i++) {
				arms[i] = body.getChild("arm" + i);
			}
			this.pendulum = body.getChild("pendulum");
			ModelPart wheel = root.getChild("wheel");
			this.ringA = wheel.getChild("ring_a");
			this.ringB = wheel.getChild("ring_b_frame").getChild("ring_b");
		}

		public static LayerDefinition createLayer() {
			MeshDefinition mesh = new MeshDefinition();
			PartDefinition root = mesh.getRoot();
			// колесо-престол: центр на 11 пикселей над землёй, два кольца крест-накрест
			PartDefinition wheel = root.addOrReplaceChild("wheel", CubeListBuilder.create(), PartPose.offset(0, 11, 0));
			PartDefinition ringA = wheel.addOrReplaceChild("ring_a", CubeListBuilder.create(), PartPose.ZERO);
			// второе кольцо повёрнуто на 90° вокруг вертикали; крутится вложенная часть — вокруг собственной оси кольца
			PartDefinition ringB = wheel.addOrReplaceChild("ring_b_frame", CubeListBuilder.create(), PartPose.rotation(0, Mth.HALF_PI, 0))
				.addOrReplaceChild("ring_b", CubeListBuilder.create(), PartPose.ZERO);
			for (PartDefinition ring : new PartDefinition[] {ringA, ringB}) {
				for (int i = 0; i < SEGMENTS; i++) {
					float a = i * Mth.TWO_PI / SEGMENTS;
					CubeListBuilder seg = CubeListBuilder.create().texOffs(0, 56).addBox(-1.5F, -2.6F, -1.5F, 3, 5.2F, 3);
					if (i % 4 == 0) {
						seg.texOffs(14, 56).addBox(-1.0F, -1.0F, -2.2F, 2, 2, 1);  // око на ободе
						seg.texOffs(14, 56).addBox(-1.0F, -1.0F, 1.2F, 2, 2, 1);
					}
					ring.addOrReplaceChild("seg" + i, seg, PartPose.offsetAndRotation(Mth.sin(a) * WHEEL_R, -Mth.cos(a) * WHEEL_R, 0, 0, 0, a));
				}
			}
			// корпус сидит на ободе
			PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create()
				.texOffs(0, 0).addBox(-6, -14, -3.5F, 12, 14, 7)
				.texOffs(0, 22).addBox(-5, 0, -3, 10, 6, 6), PartPose.offset(0, -8, 0));
			PartDefinition head = body.addOrReplaceChild("head", CubeListBuilder.create().texOffs(40, 0).addBox(-5, -10, -2, 10, 10, 4),
				PartPose.offset(0, -14, 0));
			head.addOrReplaceChild("hour_hand", CubeListBuilder.create().texOffs(70, 0).addBox(-0.5F, -3.5F, -0.5F, 1, 4, 1),
				PartPose.offset(0, -5, -2.4F));
			head.addOrReplaceChild("minute_hand", CubeListBuilder.create().texOffs(76, 0).addBox(-0.5F, -5.0F, -0.5F, 1, 6, 1),
				PartPose.offset(0, -5, -2.6F));
			head.addOrReplaceChild("halo", CubeListBuilder.create().texOffs(40, 16).addBox(-7, -7, 0, 14, 14, 1), PartPose.offset(0, -5, 2.6F));
			float[][] shoulders = {{7, -13, -0.6F}, {-7, -13, 0.6F}, {6, -6, -1.1F}, {-6, -6, 1.1F}};
			for (int i = 0; i < 4; i++) {
				PartDefinition arm = body.addOrReplaceChild("arm" + i, CubeListBuilder.create().texOffs(0, 36).addBox(-1.5F, 0, -1.5F, 3, 10, 3),
					PartPose.offsetAndRotation(shoulders[i][0], shoulders[i][1], 0, 0, 0, shoulders[i][2]));
				arm.addOrReplaceChild("blade", CubeListBuilder.create().texOffs(14, 36).addBox(-1, 0, -0.5F, 2, 16, 1), PartPose.offset(0, 9, 0));
			}
			PartDefinition pendulum = body.addOrReplaceChild("pendulum", CubeListBuilder.create().texOffs(24, 36).addBox(-0.5F, 0, -0.5F, 1, 8, 1),
				PartPose.offset(0, 6, 0));
			pendulum.addOrReplaceChild("bob", CubeListBuilder.create().texOffs(30, 36).addBox(-2, 0, -0.5F, 4, 4, 1), PartPose.offset(0, 8, 0));
			return LayerDefinition.create(mesh, 128, 128);
		}

		@Override
		public void setupAnim(State state) {
			super.setupAnim(state);
			float t = state.ageInTicks;
			float wheelSpeed = state.phase == 3 ? -0.05F : 0.03F;  // в «Перемотке» колесо крутится назад
			ringA.zRot = t * wheelSpeed;
			ringB.zRot = -t * wheelSpeed * 0.8F;
			body.y = -8 + Mth.sin(t * 0.07F) * 0.8F;
			body.yRot = state.sweep * Mth.TWO_PI;  // взмах — полный оборот корпуса
			head.xRot = state.xRot * Mth.DEG_TO_RAD * 0.5F;
			float minute = state.warning ? 0 : t * 0.08F;
			minuteHand.zRot = -minute;
			hourHand.zRot = state.warning ? 0 : -minute / 12.0F - 1.2F;
			halo.zRot = t * 0.04F;
			for (int i = 0; i < 4; i++) {
				float side = (i % 2 == 0) ? 1 : -1;
				float base = i < 2 ? 0.6F : 1.1F;
				float lift = state.sweep > 0 ? Mth.sin(state.sweep * Mth.PI) * 1.2F : 0;
				arms[i].zRot = side * (-base - lift) + Mth.sin(t * 0.06F + i) * 0.05F;
				arms[i].xRot = -0.2F + Mth.sin(t * 0.05F + i * 1.3F) * 0.08F;
			}
			pendulum.zRot = Mth.sin(t * (state.phase == 3 ? 0.25F : 0.15F)) * 0.45F;
		}
	}

	static class Boss extends MobRenderer<Clockmaker, State, Model> {
		private static final Identifier TEXTURE = Celestial.id("textures/entity/clockmaker.png");

		Boss(EntityRendererProvider.Context ctx) {
			super(ctx, new Model(ctx.bakeLayer(LAYER)), 1.8F);
			addLayer(new AbyssRenderers.GlowLayer<>(this, Celestial.id("textures/entity/clockmaker_glow.png")));
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
		public void extractRenderState(Clockmaker entity, State state, float partialTicks) {
			super.extractRenderState(entity, state, partialTicks);
			state.phase = entity.phase();
			int sw = entity.sweeping();
			state.sweep = sw > 0 ? 1.0F - Math.max(0, sw - partialTicks) / 14.0F : 0;
			state.warning = entity.warning() > 0;
		}

		@Override
		protected void scale(State state, PoseStack poseStack) {
			poseStack.scale(1.3F, 1.3F, 1.3F);
		}
	}
}
