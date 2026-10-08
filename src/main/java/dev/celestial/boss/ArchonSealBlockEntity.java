package dev.celestial.boss;

import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModEntities;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/** Пробуждение Морозного Архонта: вспышка инея, столб снега, титры с именем и короткая слепота метели. */
public class ArchonSealBlockEntity extends BlockEntity {
	private static final double WAKE_RADIUS = 9.0;

	public ArchonSealBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.ARCHON_SEAL, pos, state);
	}

	public static void serverTick(Level level, BlockPos pos, BlockState state, ArchonSealBlockEntity seal) {
		if (level.getGameTime() % 10 != 0 || !(level instanceof ServerLevel server)) {
			return;
		}
		Player player = level.getNearestPlayer(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, WAKE_RADIUS,
			p -> !p.isSpectator() && !((Player) p).isCreative());
		if (player == null) {
			if (level.getRandom().nextInt(3) == 0) {
				server.sendParticles(ParticleTypes.SNOWFLAKE, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5, 4, 0.4, 0.3, 0.4, 0.01);
			}
			return;
		}
		awaken(server, pos, state);
	}

	public static void awaken(ServerLevel level, BlockPos pos, BlockState state) {
		level.setBlock(pos, state.setValue(ArchonSealBlock.AWAKENED, true), Block.UPDATE_ALL);
		FrostArchon boss = ModEntities.FROST_ARCHON.create(level, EntitySpawnReason.TRIGGERED);
		if (boss == null) {
			return;
		}
		boss.snapTo(pos.getX() + 0.5, pos.getY() + 1, pos.getZ() + 0.5, 0, 0);
		boss.setHome(pos);
		level.addFreshEntity(boss);
		for (int i = 0; i < 30; i++) {  // столб снега и света из печати
			level.sendParticles(ParticleTypes.SNOWFLAKE, pos.getX() + 0.5, pos.getY() + 1 + i * 0.4, pos.getZ() + 0.5, 12, 0.4, 0.2, 0.4, 0.05);
			level.sendParticles(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 1 + i * 0.4, pos.getZ() + 0.5, 2, 0.2, 0.2, 0.2, 0.02);
		}
		level.sendParticles(ParticleTypes.SNOWFLAKE, pos.getX() + 0.5, pos.getY() + 3, pos.getZ() + 0.5, 400, 8, 3, 8, 0.25);
		level.playSound(null, pos, SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 4.0F, 1.5F);
		level.playSound(null, pos, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 4.0F, 0.4F);
		for (ServerPlayer p : level.getPlayers(p -> p.distanceToSqr(Vec3.atCenterOf(pos)) < 48 * 48)) {
			p.sendSystemMessage(Component.translatable("boss.celestial.frost_archon.awaken"));
			p.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 25, 0, false, false));
			p.connection.send(new ClientboundSetTitlesAnimationPacket(10, 70, 20));
			p.connection.send(new ClientboundSetTitleTextPacket(Component.translatable("entity.celestial.frost_archon").withStyle(ChatFormatting.AQUA)));
			p.connection.send(new ClientboundSetSubtitleTextPacket(Component.translatable("boss.celestial.frost_archon.subtitle")));
		}
	}
}
