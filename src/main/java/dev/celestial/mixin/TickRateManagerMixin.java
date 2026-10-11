package dev.celestial.mixin;

import dev.celestial.chrono.TimeFlow;
import net.minecraft.world.TickRateManager;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Ход времени: сущность в стоп- или замедляющей зоне пропускает тик (и на сервере, и на клиенте — там только полная остановка). */
@Mixin(TickRateManager.class)
public class TickRateManagerMixin {
	@Inject(method = "isEntityFrozen", at = @At("HEAD"), cancellable = true)
	private void celestial$timeFlow(Entity entity, CallbackInfoReturnable<Boolean> cir) {
		if (TimeFlow.skipTick(entity)) {
			cir.setReturnValue(true);
		}
	}
}
