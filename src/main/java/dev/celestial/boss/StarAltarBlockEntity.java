package dev.celestial.boss;

import dev.celestial.astral.Choirs;
import dev.celestial.data.CelestialData;
import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModEntities;
import dev.celestial.registry.ModParticles;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/** Пробуждение Безликого: хоры поют, звёзды над алтарём гаснут одна за другой, из темноты встаёт фигура без лица. */
public class StarAltarBlockEntity extends BlockEntity {
	public static final int CHOIRS_NEEDED = 7;
	private static final double WAKE_RADIUS = 9.0;
	private int messageCooldown;

	public StarAltarBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.STAR_ALTAR, pos, state);
	}

	public static void serverTick(Level level, BlockPos pos, BlockState state, StarAltarBlockEntity altar) {
		if (level.getGameTime() % 10 != 0 || !(level instanceof ServerLevel server)) {
			return;
		}
		if (altar.messageCooldown > 0) {
			altar.messageCooldown--;
		}
		Vec3 c = Vec3.atCenterOf(pos);
		for (ServerPlayer p : server.getPlayers(p -> !p.isSpectator() && !p.isCreative() && p.position().distanceTo(c) < WAKE_RADIUS)) {
			int choirs = Choirs.count(CelestialData.get(p));
			if (choirs >= CHOIRS_NEEDED) {
				awaken(server, pos, state);
				return;
			}
			if (altar.messageCooldown == 0) {
				p.sendOverlayMessage(Component.translatable("block.celestial.star_altar.silent", choirs, CHOIRS_NEEDED));
				altar.messageCooldown = 8;
			}
		}
		if (level.getRandom().nextInt(3) == 0) {
			server.sendParticles(ModParticles.STARLIGHT, pos.getX() + 0.5, pos.getY() + 1.4, pos.getZ() + 0.5, 3, 0.6, 0.3, 0.6, 0.02);
		}
	}

	public static void awaken(ServerLevel level, BlockPos pos, BlockState state) {
		level.setBlock(pos, state.setValue(StarAltarBlock.AWAKENED, true), Block.UPDATE_ALL);
		Faceless boss = ModEntities.FACELESS.create(level, EntitySpawnReason.TRIGGERED);
		if (boss == null) {
			return;
		}
		boss.snapTo(pos.getX() + 0.5, pos.getY() + 3, pos.getZ() + 0.5, 0, 0);
		boss.setHome(pos);
		level.addFreshEntity(boss);
		for (int i = 0; i < 30; i++) {  // столб тьмы, гаснущие звёзды
			level.sendParticles(ModParticles.SHADOW, pos.getX() + 0.5, pos.getY() + 1 + i * 0.4, pos.getZ() + 0.5, 10, 0.5, 0.2, 0.5, 0.03);
		}
		level.sendParticles(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 8, pos.getZ() + 0.5, 300, 10, 4, 10, 0.05);
		level.playSound(null, pos, SoundEvents.WITHER_SPAWN, SoundSource.HOSTILE, 4.0F, 0.6F);
		level.playSound(null, pos, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 6.0F, 0.5F);
		for (ServerPlayer p : level.getPlayers(p -> p.distanceToSqr(Vec3.atCenterOf(pos)) < 64 * 64)) {
			p.sendSystemMessage(Component.translatable("boss.celestial.faceless.awaken"));
		}
		BossIntro.awaken(level, pos, "faceless", ChatFormatting.DARK_PURPLE, 64);
	}
}
