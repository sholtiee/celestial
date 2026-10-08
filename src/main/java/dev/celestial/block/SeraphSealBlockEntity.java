package dev.celestial.block;

import dev.celestial.entity.FallenSeraph;
import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModEntities;
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

public class SeraphSealBlockEntity extends BlockEntity {
	private static final double WAKE_RADIUS = 12.0;

	public SeraphSealBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.SERAPH_SEAL, pos, state);
	}

	public static void serverTick(Level level, BlockPos pos, BlockState state, SeraphSealBlockEntity seal) {
		if (level.getGameTime() % 20 != 0 || !(level instanceof ServerLevel serverLevel)) {
			return;
		}
		Player player = level.getNearestPlayer(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, WAKE_RADIUS,
			p -> !p.isSpectator() && !((Player) p).isCreative());  // как у Печати Пожирателя: строителя в творческом не будит (BUG-035)
		if (player == null) {
			if (level.getRandom().nextInt(3) == 0) {
				serverLevel.sendParticles(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5, 3, 0.2, 0.3, 0.2, 0.01);
			}
			return;
		}
		awaken(serverLevel, pos, state);
	}

	public static void awaken(ServerLevel level, BlockPos pos, BlockState state) {
		level.setBlock(pos, state.setValue(SeraphSealBlock.AWAKENED, true), Block.UPDATE_ALL);
		FallenSeraph seraph = ModEntities.FALLEN_SERAPH.create(level, EntitySpawnReason.TRIGGERED);
		if (seraph == null) {
			return;
		}
		seraph.snapTo(pos.getX() + 0.5, pos.getY() + 2, pos.getZ() + 0.5, 0, 0);
		seraph.setHome(pos);
		level.addFreshEntity(seraph);
		level.sendParticles(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 2, pos.getZ() + 0.5, 150, 1.5, 2.5, 1.5, 0.3);
		level.playSound(null, pos, SoundEvents.WITHER_SPAWN, SoundSource.HOSTILE, 3.0F, 1.4F);
		for (ServerPlayer p : level.getPlayers(p -> p.distanceToSqr(net.minecraft.world.phys.Vec3.atCenterOf(pos)) < 64 * 64)) {
			p.sendSystemMessage(Component.translatable("boss.celestial.fallen_seraph.awaken"));
		}
		dev.celestial.boss.BossIntro.awaken(level, pos, "fallen_seraph", net.minecraft.ChatFormatting.GOLD, 64);
	}
}
