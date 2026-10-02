package dev.celestial.client.mixin;

import dev.celestial.registry.ModSounds;
import net.minecraft.client.Minecraft;
import net.minecraft.sounds.Music;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Музыка битвы: если на экране полоса босса Celestial с флагом музыки (не в Энде, где играет ванильная), звучит своя тема. */
@Mixin(Minecraft.class)
public abstract class BossMusicMixin {
	private static final Music SERAPH_BATTLE = new Music(ModSounds.MUSIC_SERAPH_BATTLE, 0, 0, true);

	@Inject(method = "getSituationalMusic", at = @At("HEAD"), cancellable = true)
	private void celestial$bossMusic(CallbackInfoReturnable<Music> cir) {
		Minecraft mc = (Minecraft) (Object) this;
		if (mc.player != null && mc.gui.screen() == null && mc.player.level().dimension() != Level.END
			&& mc.gui.hud.getBossOverlay().shouldPlayMusic()) {
			cir.setReturnValue(SERAPH_BATTLE);
		}
	}
}
