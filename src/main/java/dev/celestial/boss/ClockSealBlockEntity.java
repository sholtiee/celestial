package dev.celestial.boss;

import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModEntities;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/** Пробуждение Часовщика: бьют часы, из циферблата поднимается колесо-престол, титр с именем. */
public class ClockSealBlockEntity extends BlockEntity {
	private static final double WAKE_RADIUS = 9.0;

	public ClockSealBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.CLOCK_SEAL, pos, state);
	}

	public static void serverTick(Level level, BlockPos pos, BlockState state, ClockSealBlockEntity seal) {
		if (level.getGameTime() % 10 != 0 || !(level instanceof ServerLevel server)) {
			return;
		}
		Player player = level.getNearestPlayer(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, WAKE_RADIUS,
			p -> !p.isSpectator() && !((Player) p).isCreative());
		if (player == null) {
			if (level.getRandom().nextInt(3) == 0) {
				server.sendParticles(dev.celestial.registry.ModParticles.CHRONO_HASTE, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5, 3, 0.6, 0.2, 0.6, 0.02);
			}
			return;
		}
		awaken(server, pos, state);
	}

	public static void awaken(ServerLevel level, BlockPos pos, BlockState state) {
		level.setBlock(pos, state.setValue(ClockSealBlock.AWAKENED, true), Block.UPDATE_ALL);
		Clockmaker boss = ModEntities.CLOCKMAKER.create(level, EntitySpawnReason.TRIGGERED);
		if (boss == null) {
			return;
		}
		boss.snapTo(pos.getX() + 0.5, pos.getY() + 2, pos.getZ() + 0.5, 0, 0);
		boss.setHome(pos);
		level.addFreshEntity(boss);
		for (int i = 0; i < 30; i++) {  // столб искр-шестерёнок из циферблата
			level.sendParticles(dev.celestial.registry.ModParticles.CHRONO_HASTE, pos.getX() + 0.5, pos.getY() + 1 + i * 0.4, pos.getZ() + 0.5,
				8, 0.5, 0.2, 0.5, 0.05);
		}
		level.sendParticles(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 3, pos.getZ() + 0.5, 200, 6, 3, 6, 0.2);
		for (int k = 0; k < 3; k++) {  // три удара часов
			level.playSound(null, pos, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 4.0F, 0.5F + k * 0.05F);
		}
		level.playSound(null, pos, SoundEvents.IRON_GOLEM_REPAIR, SoundSource.HOSTILE, 3.0F, 0.5F);
		for (ServerPlayer p : level.getPlayers(p -> p.distanceToSqr(Vec3.atCenterOf(pos)) < 48 * 48)) {
			p.sendSystemMessage(Component.translatable("boss.celestial.clockmaker.awaken"));
		}
		BossIntro.awaken(level, pos, "clockmaker", ChatFormatting.GOLD, 48);
	}
}
