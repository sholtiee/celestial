package dev.celestial.client.render;

import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.util.Mth;

/** Облачная медуза: полупрозрачный купол и четыре колышущихся щупальца. Текстура 64×64. */
public class CloudJellyModel extends EntityModel<LivingEntityRenderState> {
	private final ModelPart dome;
	private final ModelPart[] tentacles = new ModelPart[4];

	public CloudJellyModel(ModelPart root) {
		super(root, RenderTypes::entityTranslucent);
		this.dome = root.getChild("dome");
		for (int i = 0; i < 4; i++) {
			tentacles[i] = root.getChild("tentacle" + i);
		}
	}

	public static LayerDefinition createBodyLayer() {
		MeshDefinition mesh = new MeshDefinition();
		PartDefinition root = mesh.getRoot();
		root.addOrReplaceChild("dome", CubeListBuilder.create().texOffs(0, 0).addBox(-8.0F, -8.0F, -8.0F, 16.0F, 8.0F, 16.0F)
			.texOffs(0, 24).addBox(-6.0F, -11.0F, -6.0F, 12.0F, 3.0F, 12.0F), PartPose.offset(0.0F, 12.0F, 0.0F));
		int[][] spots = {{-5, -5}, {5, -5}, {-5, 5}, {5, 5}};
		for (int i = 0; i < 4; i++) {
			root.addOrReplaceChild("tentacle" + i, CubeListBuilder.create().texOffs(48, 24).addBox(-1.0F, 0.0F, -1.0F, 2.0F, 11.0F, 2.0F),
				PartPose.offset(spots[i][0], 12.0F, spots[i][1]));
		}
		return LayerDefinition.create(mesh, 64, 64);
	}

	@Override
	public void setupAnim(LivingEntityRenderState state) {
		super.setupAnim(state);
		float t = state.ageInTicks;
		dome.y = 12.0F + Mth.sin(t * 0.1F) * 1.0F;
		for (int i = 0; i < 4; i++) {
			tentacles[i].xRot = Mth.sin(t * 0.15F + i) * 0.3F;
			tentacles[i].zRot = Mth.cos(t * 0.13F + i * 1.7F) * 0.3F;
			tentacles[i].y = dome.y;
		}
	}
}
