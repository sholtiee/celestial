package dev.celestial.client.chrono;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.celestial.Celestial;
import dev.celestial.chrono.PendulumBlock;
import dev.celestial.chrono.PendulumBlockEntity;
import dev.celestial.registry.ModBlocks;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.minecraft.client.model.Model;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.Direction;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.util.Unit;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Маятник под корпусом: латунный стержень, шарнир и диск-груз качаются в плоскости лицевой стороны.
 * Если под корпусом опора — маятник стоит сверху, как метроном. Остановленный висит отвесно.
 */
public class PendulumRenderer implements BlockEntityRenderer<PendulumBlockEntity, PendulumRenderer.State> {
	public static final ModelLayerLocation LAYER = new ModelLayerLocation(Celestial.id("pendulum"), "main");
	private static final Identifier SWIFT = Celestial.id("textures/entity/chrono/pendulum_swift.png");
	private static final Identifier HEAVY = Celestial.id("textures/entity/chrono/pendulum_heavy.png");

	public static class State extends BlockEntityRenderState {
		float angle;
		boolean upright;
		boolean swift;
		Direction facing = Direction.NORTH;
	}

	private final Model.Simple model;

	public PendulumRenderer(BlockEntityRendererProvider.Context ctx) {
		this.model = new Model.Simple(ctx.bakeLayer(LAYER), RenderTypes::entityCutout);
	}

	public static void register() {
		ModelLayerRegistry.registerModelLayer(LAYER, PendulumRenderer::createLayer);
		net.fabricmc.fabric.api.client.rendering.v1.BlockEntityRendererRegistry.register(
			dev.celestial.registry.ModBlockEntities.PENDULUM, PendulumRenderer::new);
	}

	/** Стержень вниз от шарнира (y=0), груз — диск 7×7 с ободом. Текстура 32×32. */
	static LayerDefinition createLayer() {
		MeshDefinition mesh = new MeshDefinition();
		PartDefinition root = mesh.getRoot();
		root.addOrReplaceChild("hinge", CubeListBuilder.create().texOffs(0, 24).addBox(-1.5F, -1.5F, -1.5F, 3, 3, 3), PartPose.ZERO);
		root.addOrReplaceChild("rod", CubeListBuilder.create().texOffs(0, 0).addBox(-0.5F, -19.0F, -0.5F, 1, 18, 1), PartPose.ZERO);
		root.addOrReplaceChild("bob", CubeListBuilder.create()
			.texOffs(4, 0).addBox(-3.5F, -25.0F, -1.0F, 7, 7, 2)
			.texOffs(4, 9).addBox(-2.5F, -26.0F, -1.0F, 5, 1, 2)
			.texOffs(4, 9).addBox(-2.5F, -18.0F, -1.0F, 5, 1, 2)
			.texOffs(4, 12).addBox(-4.5F, -24.0F, -1.0F, 1, 5, 2)
			.texOffs(4, 12).addBox(3.5F, -24.0F, -1.0F, 1, 5, 2)
			.texOffs(12, 12).addBox(-1.5F, -23.0F, -1.5F, 3, 3, 3), PartPose.ZERO);
		return LayerDefinition.create(mesh, 32, 32);
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(PendulumBlockEntity be, State state, float partialTicks, Vec3 camera,
		ModelFeatureRenderer.@Nullable CrumblingOverlay breakProgress) {
		BlockEntityRenderer.super.extractRenderState(be, state, partialTicks, camera, breakProgress);
		BlockState block = be.getBlockState();
		state.swift = block.is(ModBlocks.SWIFT_PENDULUM);
		state.facing = block.getValue(PendulumBlock.FACING);
		state.angle = 0;
		if (be.getLevel() != null) {
			state.upright = !be.getLevel().getBlockState(be.getBlockPos().below()).isAir();
			if (block.getValue(PendulumBlock.SWINGING) && block.getBlock() instanceof PendulumBlock p) {
				float t = (be.getLevel().getGameTime() % p.period + partialTicks) / p.period;
				state.angle = Mth.sin(t * Mth.TWO_PI) * (state.upright ? 28.0F : 32.0F);
			}
		}
	}

	@Override
	public void submit(State state, PoseStack pose, SubmitNodeCollector collector, CameraRenderState camera) {
		pose.pushPose();
		if (state.upright) {
			pose.translate(0.5, 1.0, 0.5);
			pose.rotateDegrees(Axis.XP, 180);  // метроном: тот же маятник, перевёрнутый над корпусом
		} else {
			pose.translate(0.5, 0.0, 0.5);
		}
		pose.rotateDegrees(Axis.YP, -state.facing.toYRot());
		pose.rotateDegrees(Axis.ZP, state.angle);
		collector.submitModel(model, Unit.INSTANCE, pose, state.swift ? SWIFT : HEAVY, state.lightCoords, OverlayTexture.NO_OVERLAY, 0);
		pose.popPose();
	}

	@Override
	public boolean shouldRenderOffScreen() {
		return true;
	}
}
