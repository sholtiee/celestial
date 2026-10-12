package dev.celestial.world.portal;

import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.gameevent.GameEvent;

/** Зажигание рамки предметом-активатором (используется предметами-ключами порталов). */
public final class PortalActivation {
	private PortalActivation() {}

	/**
	 * Порталы, чьи ключи — обычные реликвии (Ледяная Корона, Шестерня Вечности), а не предметы со своим useOn: зажигаем кликом по рамке.
	 */
	public static void init() {
		net.fabricmc.fabric.api.event.player.UseBlockCallback.EVENT.register((player, level, hand, hit) -> {
			var stack = player.getItemInHand(hand);
			if (!stack.is(dev.celestial.registry.ModItems.ICE_CROWN) && !stack.is(dev.celestial.registry.ModItems.GEAR_OF_ETERNITY)) {
				return InteractionResult.PASS;
			}
			return tryActivate(new UseOnContext(player, hand, hit), () -> { });
		});
	}

	public static InteractionResult tryActivate(UseOnContext context, Runnable onLit) {
		Level level = context.getLevel();
		BlockPos clicked = context.getClickedPos();
		for (PortalType type : PortalTypes.ALL) {
			if (!context.getItemInHand().is(type.activator().get()) || !type.isFrame(level.getBlockState(clicked))) {
				continue;
			}
			Optional<PortalShape> shape = PortalShape.find(type, level, clicked.relative(context.getClickedFace()));
			if (shape.isEmpty()) {
				return InteractionResult.FAIL;
			}
			if (level instanceof ServerLevel serverLevel) {
				shape.get().fill(serverLevel);
				serverLevel.playSound(null, clicked, SoundEvents.END_PORTAL_SPAWN, SoundSource.BLOCKS, 0.6F, 1.6F);
				serverLevel.gameEvent(context.getPlayer(), GameEvent.BLOCK_PLACE, clicked);
				onLit.run();
			}
			return InteractionResult.SUCCESS;
		}
		return InteractionResult.PASS;
	}
}
