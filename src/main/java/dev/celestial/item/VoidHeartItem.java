package dev.celestial.item;

import dev.celestial.world.HeavenPortalShape;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.gameevent.GameEvent;

/** Сердце Пустоты: зажигает рамку из светлого камня, сам не расходуется. */
public class VoidHeartItem extends Item {
	public VoidHeartItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult useOn(UseOnContext context) {
		Level level = context.getLevel();
		BlockPos clicked = context.getClickedPos();
		if (!HeavenPortalShape.isFrame(level.getBlockState(clicked))) {
			return InteractionResult.PASS;
		}
		Optional<HeavenPortalShape> shape = HeavenPortalShape.find(level, clicked.relative(context.getClickedFace()));
		if (shape.isEmpty()) {
			return InteractionResult.FAIL;
		}
		if (level instanceof ServerLevel serverLevel) {
			shape.get().fill(serverLevel);
			serverLevel.playSound(null, clicked, SoundEvents.END_PORTAL_SPAWN, SoundSource.BLOCKS, 0.6F, 1.6F);
			serverLevel.gameEvent(context.getPlayer(), GameEvent.BLOCK_PLACE, clicked);
			if (context.getPlayer() != null) {
				dev.celestial.story.StoryEvents.onHeavenPortalLit(context.getPlayer());
			}
		}
		return InteractionResult.SUCCESS;
	}
}
