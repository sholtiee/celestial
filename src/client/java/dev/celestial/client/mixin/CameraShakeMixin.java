package dev.celestial.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.celestial.client.CameraShake;
import net.minecraft.client.renderer.GameRenderer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Тряска камеры (пробуждение босса, смена фаз): добавляется к ванильному покачиванию от урона. */
@Mixin(GameRenderer.class)
public abstract class CameraShakeMixin {
	@Inject(method = "bobHurt", at = @At("TAIL"))
	private void celestial$shake(net.minecraft.client.renderer.state.level.CameraRenderState cameraState, PoseStack poseStack, CallbackInfo ci) {
		CameraShake.apply(poseStack);
	}
}
