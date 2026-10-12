package dev.celestial.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.renderpearl.api.commands.RenderPass;
import net.minecraft.client.renderer.SkyRenderer;
import net.minecraft.world.level.MoonPhase;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

@Mixin(SkyRenderer.class)
public interface SkyRendererInvoker {
	@Invoker("renderSunMoonAndStars")
	void celestial$sunMoonAndStars(RenderPass pass, PoseStack pose, float sun, float moon, float star, MoonPhase phase, float rain, float starBrightness);
}
