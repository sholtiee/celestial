package dev.celestial.client.render;

import net.minecraft.client.model.animal.equine.AbstractEquineModel;
import net.minecraft.client.model.animal.equine.HorseModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.entity.state.EquineRenderState;
import net.minecraft.util.Mth;

/** Лошадиная модель с парой крыльев на спине (текстура 128×64, крылья в правой половине). */
public class PegasusModel extends HorseModel {
	private final ModelPart leftWing;
	private final ModelPart rightWing;

	public PegasusModel(ModelPart root) {
		super(root);
		this.leftWing = root.getChild("body").getChild("left_wing");
		this.rightWing = root.getChild("body").getChild("right_wing");
	}

	public static LayerDefinition createBodyLayer() {
		MeshDefinition mesh = AbstractEquineModel.createBodyMesh(CubeDeformation.NONE);
		PartDefinition body = mesh.getRoot().getChild("body");
		body.addOrReplaceChild("left_wing", CubeListBuilder.create().texOffs(64, 0).addBox(0.0F, -1.0F, -6.0F, 16.0F, 1.0F, 12.0F),
			PartPose.offset(4.5F, -7.0F, -9.0F));
		body.addOrReplaceChild("right_wing", CubeListBuilder.create().texOffs(64, 16).addBox(-16.0F, -1.0F, -6.0F, 16.0F, 1.0F, 12.0F),
			PartPose.offset(-4.5F, -7.0F, -9.0F));
		return LayerDefinition.create(mesh, 128, 64).apply(net.minecraft.client.model.geom.builders.MeshTransformer.scaling(1.1F));
	}

	@Override
	public void setupAnim(EquineRenderState state) {
		super.setupAnim(state);
		// в полёте под седоком машет быстро, на земле — лениво сложены
		float speed = state.isRidden ? 0.45F : 0.08F;
		float amplitude = state.isRidden ? 0.7F : 0.15F;
		float flap = Mth.sin(state.ageInTicks * speed) * amplitude;
		leftWing.zRot = -0.25F - flap;
		rightWing.zRot = 0.25F + flap;
	}
}
