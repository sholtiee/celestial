package dev.celestial.block.machine;

import dev.celestial.data.CelestialData;
import dev.celestial.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.portal.TeleportTransition;
import net.minecraft.world.phys.Vec3;

/** Перенос по сети маяков: игрок должен стоять у маяка, цель должна быть в сети и существовать. */
public final class BeaconTravel {
	private BeaconTravel() {}

	public static int travel(ServerPlayer player, BlockPos target, Identifier dimension) {
		if (!nearBeacon(player)) {
			player.sendOverlayMessage(Component.translatable("machine.celestial.beacon.too_far"));
			return 0;
		}
		boolean known = CelestialData.beacons(player.level().getServer()).beacons().stream()
			.anyMatch(b -> b.pos().equals(target) && b.dimension().equals(dimension.toString()))
			&& SkyBeaconBlock.known(player, dimension.toString(), target);  // переносит только к открытым самим игроком маякам
		ServerLevel level = player.level().getServer().getLevel(ResourceKey.create(Registries.DIMENSION, dimension));
		if (!known || level == null || !level.getBlockState(target).is(ModBlocks.SKY_BEACON)) {
			player.sendOverlayMessage(Component.translatable("machine.celestial.beacon.lost"));
			if (level != null && known) {
				CelestialData.updateBeacons(player.level().getServer(), n -> n.without(dimension.toString(), target));
			}
			return 0;
		}
		player.level().playSound(null, player.blockPosition(), SoundEvents.ENDERMAN_TELEPORT, SoundSource.PLAYERS, 1.0F, 1.4F);
		player.teleport(new TeleportTransition(level, Vec3.atBottomCenterOf(target.above()), Vec3.ZERO, player.getYRot(), player.getXRot(),
			TeleportTransition.PLAY_PORTAL_SOUND));
		level.sendParticles(ParticleTypes.END_ROD, target.getX() + 0.5, target.getY() + 1.5, target.getZ() + 0.5, 40, 0.4, 0.8, 0.4, 0.05);
		return 1;
	}

	private static boolean nearBeacon(ServerPlayer player) {
		BlockPos at = player.blockPosition();
		for (BlockPos p : BlockPos.betweenClosed(at.offset(-4, -3, -4), at.offset(4, 3, 4))) {
			if (player.level().getBlockState(p).is(ModBlocks.SKY_BEACON)) {
				return true;
			}
		}
		return false;
	}
}
