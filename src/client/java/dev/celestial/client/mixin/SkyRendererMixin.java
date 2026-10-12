package dev.celestial.client.mixin;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.renderpearl.api.commands.RenderPass;
import dev.celestial.client.sky.CelestialSky;
import net.minecraft.client.Camera;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.SkyRenderer;
import net.minecraft.client.renderer.state.level.SkyRenderState;
import net.minecraft.client.renderer.texture.TextureAtlas;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.Redirect;

/**
 * Небо измерений мода: правка состояния (звёзды днём в Раю, тёмный Рай после «Поглотить») и свои небесные тела после солнца,
 * луны и звёзд (ореол солнца и полярное сияние Рая, туманности и созвездия хоров в Астрале) — {@link CelestialSky}.
 */
@Mixin(SkyRenderer.class)
public abstract class SkyRendererMixin {
	@Shadow
	@Final
	private TextureAtlas celestialsAtlas;

	@Shadow
	@Final
	private RenderSystem.AutoStorageIndexBuffer quadIndices;

	@Inject(method = "extractRenderState", at = @At("TAIL"))
	private void celestial$extract(ClientLevel level, float partialTicks, Camera camera, SkyRenderState state, CallbackInfo ci) {
		CelestialSky.extract(level, state);
	}

	@Redirect(method = "render", at = @At(value = "INVOKE",
		target = "Lnet/minecraft/client/renderer/SkyRenderer;renderSunMoonAndStars(Lcom/mojang/renderpearl/api/commands/RenderPass;Lcom/mojang/blaze3d/vertex/PoseStack;FFFLnet/minecraft/world/level/MoonPhase;FF)V"))
	private void celestial$bodies(SkyRenderer self, RenderPass pass, com.mojang.blaze3d.vertex.PoseStack pose, float sun, float moon, float star,
		net.minecraft.world.level.MoonPhase phase, float rain, float starBrightness) {
		((SkyRendererInvoker) self).celestial$sunMoonAndStars(pass, pose, sun, moon, star, phase, rain, starBrightness);
		CelestialSky.draw(pass, celestialsAtlas, quadIndices, sun, rain);
	}
}
