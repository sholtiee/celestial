package dev.celestial.trial;

import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.BucketItem;
import net.minecraft.world.level.Level;

/** Пока идёт испытание на ловкость (паркур), рядом с ним нельзя строить: мост или столб из блоков обходили пропасть. */
public final class TrialGuard {
	private static final int RADIUS = 24;

	private record Active(ResourceKey<Level> dimension, BlockPos pos) {}

	private static final List<Active> ACTIVE = new ArrayList<>();

	private TrialGuard() {}

	public static void init() {
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> ACTIVE.clear());
		UseBlockCallback.EVENT.register((player, level, hand, hit) -> {
			if (level instanceof ServerLevel server && !player.isCreative() && !player.isSpectator()) {
				var stack = player.getItemInHand(hand);
				if ((stack.getItem() instanceof BlockItem || stack.getItem() instanceof BucketItem) && nearParkour(server, hit.getBlockPos())) {
					player.sendOverlayMessage(Component.translatable("trial.celestial.no_build"));
					return InteractionResult.FAIL;
				}
			}
			return InteractionResult.PASS;
		});
	}

	private static boolean nearParkour(ServerLevel level, BlockPos pos) {
		for (Active a : ACTIVE) {
			if (a.dimension().equals(level.dimension()) && a.pos().distSqr(pos) < RADIUS * RADIUS) {
				return true;
			}
		}
		return false;
	}

	public static void started(ServerLevel level, BlockPos pos) {
		Active a = new Active(level.dimension(), pos.immutable());
		if (!ACTIVE.contains(a)) {
			ACTIVE.add(a);
		}
	}

	public static void ended(ServerLevel level, BlockPos pos) {
		ACTIVE.removeIf(a -> a.dimension().equals(level.dimension()) && a.pos().equals(pos));
	}
}
