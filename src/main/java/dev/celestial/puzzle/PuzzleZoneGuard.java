package dev.celestial.puzzle;

import java.util.Collections;
import java.util.Set;
import java.util.WeakHashMap;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerBlockEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.BucketItem;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;

/**
 * Охрана нерешённых загадок: загруженные {@link PuzzleZone} собираются по событиям загрузки сущностей блоков,
 * и в их объёме игрок (не в творческом режиме) не может ставить блоки и выливать вёдра.
 */
public final class PuzzleZoneGuard {
	private static final Set<BlockEntity> ZONES = Collections.newSetFromMap(new WeakHashMap<>());

	private PuzzleZoneGuard() {}

	public static void init() {
		ServerBlockEntityEvents.BLOCK_ENTITY_LOAD.register((be, level) -> {
			if (be instanceof PuzzleZone) {
				ZONES.add(be);
			}
		});
		ServerBlockEntityEvents.BLOCK_ENTITY_UNLOAD.register((be, level) -> ZONES.remove(be));
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> ZONES.clear());
		UseBlockCallback.EVENT.register((player, level, hand, hit) -> {
			if (level instanceof ServerLevel server && !player.isCreative() && !player.isSpectator()) {
				var item = player.getItemInHand(hand).getItem();
				if (server.getBlockState(hit.getBlockPos()).getBlock() instanceof PuzzleInteractive && !player.isSecondaryUseActive()) {
					return InteractionResult.PASS;
				}
				if ((item instanceof BlockItem || item instanceof BucketItem)
					&& (guarded(server, hit.getBlockPos()) || guarded(server, hit.getBlockPos().relative(hit.getDirection())))) {
					player.sendOverlayMessage(Component.translatable("puzzle.celestial.zone.no_build"));
					return InteractionResult.FAIL;
				}
			}
			return InteractionResult.PASS;
		});
	}

	public static boolean guarded(Level level, BlockPos pos) {
		for (BlockEntity be : ZONES) {
			if (!be.isRemoved() && be.getLevel() == level && be instanceof PuzzleZone zone && zone.guards(pos)) {
				return true;
			}
		}
		return false;
	}
}
