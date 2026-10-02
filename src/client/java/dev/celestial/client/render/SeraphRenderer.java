package dev.celestial.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.celestial.Celestial;
import dev.celestial.entity.FallenSeraph;
import dev.celestial.entity.SeraphCrystal;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.object.crystal.EndCrystalModel;
import net.minecraft.client.model.object.equipment.ElytraModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.culling.Frustum;
import net.minecraft.client.renderer.entity.EndCrystalRenderer;
import net.minecraft.client.renderer.entity.EnderDragonRenderer;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.EndCrystalRenderState;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/** Падший Серафим: тело на общей модели ×1.5 и две пары тёмных крыльев, медленно бьющих воздух. */
public class SeraphRenderer extends CelestialRenderers.Humanoid<FallenSeraph> {
	public SeraphRenderer(EntityRendererProvider.Context ctx) {
		super(ctx, Celestial.id("textures/entity/fallen_seraph.png"), 1.5F);
		addLayer(new Wings(this, ctx));
	}

	@Override
	public void extractRenderState(FallenSeraph entity, HumanoidRenderState state, float partialTicks) {
		super.extractRenderState(entity, state, partialTicks);
		state.chestEquipment = ItemStack.EMPTY; // крылья рисует свой слой, а не ванильный
	}

	/** Пара крыльев: поза задаётся в setupAnim, потому что модель анимируется при отложенной отрисовке (submitModel). */
	static class WingPair extends ElytraModel {
		private final ModelPart left;
		private final ModelPart right;
		private final float spread;
		private final float tilt;
		private final float phase;

		WingPair(ModelPart root, float spread, float tilt, float phase) {
			super(root);
			this.left = root.getChild("left_wing");
			this.right = root.getChild("right_wing");
			this.spread = spread;
			this.tilt = tilt;
			this.phase = phase;
		}

		@Override
		public void setupAnim(HumanoidRenderState state) {
			super.setupAnim(state);
			float flap = Mth.sin(state.ageInTicks * 0.16F - phase);
			left.xRot = tilt + 0.08F * flap;
			left.yRot = 0.2F;
			left.zRot = -spread - 0.3F * flap;
			right.xRot = left.xRot;
			right.yRot = -left.yRot;
			right.zRot = -left.zRot;
		}
	}

	static class Wings extends RenderLayer<HumanoidRenderState, HumanoidModel<HumanoidRenderState>> {
		private static final Identifier TEXTURE = Celestial.id("textures/entity/fallen_seraph_wings.png");
		private final WingPair upper;
		private final WingPair lower;

		Wings(RenderLayerParent<HumanoidRenderState, HumanoidModel<HumanoidRenderState>> parent, EntityRendererProvider.Context ctx) {
			super(parent);
			// верхняя пара — большая, раскинута в стороны; нижняя — меньше, опущена и бьёт с запаздыванием
			this.upper = new WingPair(ctx.bakeLayer(ModelLayers.ELYTRA), 1.15F, 0.3F, 0.0F);
			this.lower = new WingPair(ctx.bakeLayer(ModelLayers.ELYTRA), 0.55F, 0.6F, 0.9F);
		}

		@Override
		public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, HumanoidRenderState state, float yRot, float xRot) {
			poseStack.pushPose();
			poseStack.translate(0.0F, -0.1F, 0.15F);
			poseStack.scale(1.45F, 1.45F, 1.45F);
			renderColoredCutoutModel(upper, TEXTURE, poseStack, collector, light, state, -1, 1);
			poseStack.popPose();
			poseStack.pushPose();
			poseStack.translate(0.0F, 0.35F, 0.12F);
			poseStack.scale(1.05F, 1.05F, 1.05F);
			renderColoredCutoutModel(lower, TEXTURE, poseStack, collector, light, state, -1, 2);
			poseStack.popPose();
		}
	}

	/** Кристалл света: модель кристалла Энда в золотой текстуре и луч к Серафиму. */
	public static class Crystal extends EntityRenderer<SeraphCrystal, EndCrystalRenderState> {
		private static final Identifier TEXTURE = Celestial.id("textures/entity/seraph_crystal.png");
		private final EndCrystalModel model;

		public Crystal(EntityRendererProvider.Context ctx) {
			super(ctx);
			this.shadowRadius = 0.5F;
			this.model = new EndCrystalModel(ctx.bakeLayer(ModelLayers.END_CRYSTAL));
		}

		@Override
		public void submit(EndCrystalRenderState state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
			poseStack.pushPose();
			poseStack.scale(2.0F, 2.0F, 2.0F);
			poseStack.translate(0.0F, -0.5F, 0.0F);
			collector.submitModel(model, state, poseStack, TEXTURE, state.lightCoords, OverlayTexture.NO_OVERLAY, state.outlineColor);
			poseStack.popPose();
			Vec3 beam = state.beamOffset;
			if (beam != null) {
				float y = EndCrystalRenderer.getY(state.ageInTicks);
				poseStack.translate(beam);
				EnderDragonRenderer.submitCrystalBeams(-(float) beam.x, -(float) beam.y + y, -(float) beam.z, state.ageInTicks, poseStack, collector, state.lightCoords);
			}
			super.submit(state, poseStack, collector, camera);
		}

		@Override
		public EndCrystalRenderState createRenderState() {
			return new EndCrystalRenderState();
		}

		@Override
		public void extractRenderState(SeraphCrystal entity, EndCrystalRenderState state, float partialTicks) {
			super.extractRenderState(entity, state, partialTicks);
			state.ageInTicks = entity.time + partialTicks;
			state.showsBottom = false;
			BlockPos target = entity.getBeamTarget();
			state.beamOffset = target == null ? null : Vec3.atCenterOf(target).subtract(entity.getPosition(partialTicks));
		}

		@Override
		public boolean shouldRender(SeraphCrystal entity, Frustum culler, double camX, double camY, double camZ, float partialTicks) {
			return super.shouldRender(entity, culler, camX, camY, camZ, partialTicks) || entity.getBeamTarget() != null;
		}
	}
}
