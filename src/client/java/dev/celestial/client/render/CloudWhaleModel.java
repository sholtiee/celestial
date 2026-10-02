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

/** Облачный кит: туловище, хвост с плавником и два боковых плавника. Текстура 256×128. */
public class CloudWhaleModel extends EntityModel<LivingEntityRenderState> {
	private final ModelPart tail;
	private final ModelPart fluke;
	private final ModelPart leftFin;
	private final ModelPart rightFin;

	public CloudWhaleModel(ModelPart root) {
		super(root);
		ModelPart body = root.getChild("body");
		this.tail = body.getChild("tail");
		this.fluke = tail.getChild("fluke");
		this.leftFin = body.getChild("left_fin");
		this.rightFin = body.getChild("right_fin");
	}

	public static LayerDefinition createBodyLayer() {
		MeshDefinition mesh = new MeshDefinition();
		PartDefinition root = mesh.getRoot();
		PartDefinition body = root.addOrReplaceChild("body",
			CubeListBuilder.create().texOffs(0, 0).addBox(-12.0F, -18.0F, -24.0F, 24.0F, 18.0F, 40.0F),
			PartPose.offset(0.0F, 22.0F, 0.0F));
		PartDefinition tail = body.addOrReplaceChild("tail",
			CubeListBuilder.create().texOffs(0, 64).addBox(-6.0F, -5.0F, 0.0F, 12.0F, 10.0F, 16.0F),
			PartPose.offset(0.0F, -9.0F, 16.0F));
		tail.addOrReplaceChild("fluke",
			CubeListBuilder.create().texOffs(64, 64).addBox(-14.0F, -1.0F, 0.0F, 28.0F, 2.0F, 10.0F),
			PartPose.offset(0.0F, 0.0F, 15.0F));
		body.addOrReplaceChild("left_fin",
			CubeListBuilder.create().texOffs(160, 0).addBox(0.0F, -1.0F, -4.0F, 12.0F, 2.0F, 8.0F),
			PartPose.offset(12.0F, -4.0F, -8.0F));
		body.addOrReplaceChild("right_fin",
			CubeListBuilder.create().texOffs(160, 16).addBox(-12.0F, -1.0F, -4.0F, 12.0F, 2.0F, 8.0F),
			PartPose.offset(-12.0F, -4.0F, -8.0F));
		return LayerDefinition.create(mesh, 256, 128);
	}

	@Override
	public void setupAnim(LivingEntityRenderState state) {
		super.setupAnim(state);
		float t = state.ageInTicks * 0.08F;
		tail.xRot = Mth.sin(t) * 0.22F;
		fluke.xRot = Mth.sin(t - 0.8F) * 0.3F;
		leftFin.zRot = 0.2F + Mth.sin(t * 1.3F) * 0.25F;
		rightFin.zRot = -leftFin.zRot;
	}
}
