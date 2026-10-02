package dev.celestial.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.celestial.block.light.BeamSourceBlock;
import dev.celestial.block.light.BeamSourceBlockEntity;
import dev.celestial.light.LightBeams;
import dev.celestial.light.LightColor;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BeaconRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/** Рисует луч источника по всему пути (с отражениями и расщеплением) лучом в стиле маяка. */
public class BeamRenderer implements BlockEntityRenderer<BeamSourceBlockEntity, BeamRenderer.State> {
	public static class State extends BlockEntityRenderState {
		final List<Seg> segments = new ArrayList<>();
		float time;
	}

	record Seg(int dx, int dy, int dz, Direction dir, int length, LightColor color) {}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(BeamSourceBlockEntity be, State state, float partialTicks, Vec3 camera,
		ModelFeatureRenderer.@Nullable CrumblingOverlay breakProgress) {
		BlockEntityRenderer.super.extractRenderState(be, state, partialTicks, camera, breakProgress);
		state.segments.clear();
		BlockState block = be.getBlockState();
		if (be.getLevel() == null || !block.getValue(BeamSourceBlock.ACTIVE)) {
			return;
		}
		state.time = Math.floorMod(be.getLevel().getGameTime(), 40) + partialTicks;
		BlockPos origin = be.getBlockPos();
		LightBeams.trace(be.getLevel(), origin, block.getValue(BeamSourceBlock.FACING), LightColor.WHITE, new LightBeams.Visitor() {
			@Override
			public void segment(LightBeams.Segment s) {
				if (s.length() > 0) {
					BlockPos p = s.start();
					state.segments.add(new Seg(p.getX() - origin.getX(), p.getY() - origin.getY(), p.getZ() - origin.getZ(), s.dir(), s.length(), s.color()));
				}
			}
		});
	}

	@Override
	public void submit(State state, PoseStack pose, SubmitNodeCollector collector, CameraRenderState camera) {
		for (Seg s : state.segments) {
			pose.pushPose();
			pose.translate(s.dx() + 0.5, s.dy() + 0.5, s.dz() + 0.5);
			switch (s.dir()) {
				case DOWN -> pose.rotateDegrees(Axis.XP, 180);
				case NORTH -> pose.rotateDegrees(Axis.XP, -90);
				case SOUTH -> pose.rotateDegrees(Axis.XP, 90);
				case EAST -> pose.rotateDegrees(Axis.ZP, -90);
				case WEST -> pose.rotateDegrees(Axis.ZP, 90);
				default -> { }
			}
			pose.translate(-0.5, 0.0, -0.5);
			BeaconRenderer.submitBeaconBeam(pose, collector, BeaconRenderer.BEAM_LOCATION, 1.0F, state.time, 0, s.length(),
				0xFF000000 | s.color().rgb, 0.07F, 0.11F);
			pose.popPose();
		}
	}

	@Override
	public boolean shouldRenderOffScreen() {
		return true;
	}

	@Override
	public int getViewDistance() {
		return 96;
	}
}
