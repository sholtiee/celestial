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

/** Небесный скат: плоское тело, два широких крыла и длинный хвост. Текстура 128×64. */
public class SkyRayModel extends EntityModel<LivingEntityRenderState> {
	private final ModelPart leftWing;
	private final ModelPart rightWing;
	private final ModelPart tail;

	public SkyRayModel(ModelPart root) {
		super(root);
		ModelPart body = root.getChild("body");
		this.leftWing = body.getChild("left_wing");
		this.rightWing = body.getChild("right_wing");
		this.tail = body.getChild("tail");
	}

	public static LayerDefinition createBodyLayer() {
		MeshDefinition mesh = new MeshDefinition();
		PartDefinition body = mesh.getRoot().addOrReplaceChild("body",
			CubeListBuilder.create().texOffs(0, 0).addBox(-8.0F, -3.0F, -12.0F, 16.0F, 4.0F, 22.0F), PartPose.offset(0.0F, 20.0F, 0.0F));
		body.addOrReplaceChild("left_wing", CubeListBuilder.create().texOffs(0, 26).addBox(0.0F, -1.0F, -9.0F, 20.0F, 2.0F, 16.0F),
			PartPose.offset(8.0F, -1.0F, 0.0F));
		body.addOrReplaceChild("right_wing", CubeListBuilder.create().texOffs(0, 44).addBox(-20.0F, -1.0F, -9.0F, 20.0F, 2.0F, 16.0F),
			PartPose.offset(-8.0F, -1.0F, 0.0F));
		body.addOrReplaceChild("tail", CubeListBuilder.create().texOffs(76, 0).addBox(-1.0F, -1.0F, 0.0F, 2.0F, 2.0F, 22.0F),
			PartPose.offset(0.0F, -1.0F, 10.0F));
		return LayerDefinition.create(mesh, 128, 64);
	}

	@Override
	public void setupAnim(LivingEntityRenderState state) {
		super.setupAnim(state);
		float flap = Mth.sin(state.ageInTicks * 0.12F) * 0.35F;
		leftWing.zRot = flap;
		rightWing.zRot = -flap;
		tail.yRot = Mth.sin(state.ageInTicks * 0.08F) * 0.25F;
	}
}
