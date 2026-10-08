package dev.celestial.boss;

import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

public class DevourerSealBlockEntity extends BlockEntity {
	private static final double WAKE_RADIUS = 10.0;

	public DevourerSealBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.DEVOURER_SEAL, pos, state);
	}

	public static void serverTick(Level level, BlockPos pos, BlockState state, DevourerSealBlockEntity seal) {
		if (level.getGameTime() % 20 != 0 || !(level instanceof ServerLevel server)) {
			return;
		}
		Player player = level.getNearestPlayer(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, WAKE_RADIUS,
			p -> !p.isSpectator() && !((Player) p).isCreative());
		if (player == null) {
			if (level.getRandom().nextInt(2) == 0) {
				server.sendParticles(dev.celestial.registry.ModParticles.SHADOW, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5, 4, 0.3, 0.3, 0.3, 0.01);
			}
			return;
		}
		awaken(server, pos, state);
	}

	public static void awaken(ServerLevel level, BlockPos pos, BlockState state) {
		level.setBlock(pos, state.setValue(DevourerSealBlock.AWAKENED, true), Block.UPDATE_ALL);
		LightDevourer boss = ModEntities.LIGHT_DEVOURER.create(level, EntitySpawnReason.TRIGGERED);
		if (boss == null) {
			return;
		}
		boss.snapTo(pos.getX() + 0.5, pos.getY() + 9, pos.getZ() + 0.5, 0, 0);
		boss.setHome(pos);
		level.addFreshEntity(boss);
		level.sendParticles(dev.celestial.registry.ModParticles.SHADOW, pos.getX() + 0.5, pos.getY() + 6, pos.getZ() + 0.5, 300, 3, 3, 3, 0.1);
		level.playSound(null, pos, dev.celestial.registry.ModSounds.DEVOURER_ROAR, SoundSource.HOSTILE, 4.0F, 1.0F);
		for (ServerPlayer p : level.getPlayers(p -> p.distanceToSqr(net.minecraft.world.phys.Vec3.atCenterOf(pos)) < 64 * 64)) {
			p.sendSystemMessage(Component.translatable("boss.celestial.light_devourer.awaken"));
		}
		BossIntro.awaken(level, pos, "light_devourer", net.minecraft.ChatFormatting.DARK_PURPLE, 64);
	}
}
