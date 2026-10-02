package dev.celestial.client.render;

import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.util.Mth;

/** Огонёк: ядро и вращающаяся оболочка. */
public class LightWispModel extends EntityModel<LivingEntityRenderState> {
	private final ModelPart core;
	private final ModelPart shell;

	public LightWispModel(ModelPart root) {
		super(root);
		this.core = root.getChild("core");
		this.shell = root.getChild("shell");
	}

	public static LayerDefinition createBodyLayer() {
		MeshDefinition mesh = new MeshDefinition();
		mesh.getRoot().addOrReplaceChild("core", CubeListBuilder.create().texOffs(0, 0).addBox(-2.0F, -2.0F, -2.0F, 4.0F, 4.0F, 4.0F), PartPose.offset(0.0F, 20.0F, 0.0F));
		mesh.getRoot().addOrReplaceChild("shell", CubeListBuilder.create().texOffs(0, 8).addBox(-3.0F, -3.0F, -3.0F, 6.0F, 6.0F, 6.0F), PartPose.offset(0.0F, 20.0F, 0.0F));
		return LayerDefinition.create(mesh, 32, 32);
	}

	@Override
	public void setupAnim(LivingEntityRenderState state) {
		super.setupAnim(state);
		float t = state.ageInTicks;
		float bob = Mth.sin(t * 0.15F) * 1.5F;
		core.y = 20.0F + bob;
		shell.y = 20.0F + bob;
		shell.yRot = t * 0.1F;
		shell.xRot = t * 0.07F;
		core.yRot = -t * 0.05F;
	}
}
