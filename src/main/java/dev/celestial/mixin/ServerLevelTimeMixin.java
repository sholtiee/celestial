package dev.celestial.mixin;

import dev.celestial.chrono.TimeFlow;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Ход времени: ускоренная сущность получает лишний тик. */
@Mixin(ServerLevel.class)
public class ServerLevelTimeMixin {
	@Inject(method = "tickNonPassenger", at = @At("TAIL"))
	private void celestial$extraTick(Entity entity, CallbackInfo ci) {
		for (int i = TimeFlow.extraTicks(entity); i > 0 && !entity.isRemoved(); i--) {
			entity.tick();
		}
	}
}
