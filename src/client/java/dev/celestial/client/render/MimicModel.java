package dev.celestial.client.render;

import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.Mth;

/** Мимик: корпус сундука, крышка на петле и ряды зубов. Спящий выглядит как обычный сундук. Текстура 64×64. */
public class MimicModel extends EntityModel<MimicModel.State> {
	public static class State extends net.minecraft.client.renderer.entity.state.LivingEntityRenderState {
		public boolean awake;
	}

	private final ModelPart lid;
	private final ModelPart teeth;

	public MimicModel(ModelPart root) {
		super(root);
		this.lid = root.getChild("lid");
		this.teeth = root.getChild("teeth");
	}

	public static LayerDefinition createBodyLayer() {
		MeshDefinition mesh = new MeshDefinition();
		PartDefinition root = mesh.getRoot();
		root.addOrReplaceChild("base", CubeListBuilder.create().texOffs(0, 19).addBox(-7.0F, -10.0F, -7.0F, 14.0F, 10.0F, 14.0F),
			PartPose.offset(0.0F, 24.0F, 0.0F));
		root.addOrReplaceChild("lid", CubeListBuilder.create().texOffs(0, 0).addBox(-7.0F, -5.0F, -14.0F, 14.0F, 5.0F, 14.0F)
			.texOffs(0, 0).addBox(-1.0F, -2.0F, -15.0F, 2.0F, 4.0F, 1.0F), PartPose.offset(0.0F, 14.0F, 7.0F));
		root.addOrReplaceChild("teeth", CubeListBuilder.create().texOffs(0, 44).addBox(-6.0F, -2.0F, -6.0F, 12.0F, 2.0F, 1.0F)
			.texOffs(0, 44).addBox(-6.0F, -2.0F, 5.0F, 12.0F, 2.0F, 1.0F), PartPose.offset(0.0F, 14.0F, 0.0F));
		return LayerDefinition.create(mesh, 64, 64);
	}

	@Override
	public void setupAnim(State state) {
		super.setupAnim(state);
		if (state.awake) {
			// пасть хлопает в такт шагам и атакам
			float chomp = Math.abs(Mth.sin(state.ageInTicks * 0.35F + state.walkAnimationPos * 0.6F));
			lid.xRot = -0.15F - chomp * 0.75F;
			teeth.visible = true;
		} else {
			lid.xRot = 0.0F;
			teeth.visible = false;
		}
	}
}
