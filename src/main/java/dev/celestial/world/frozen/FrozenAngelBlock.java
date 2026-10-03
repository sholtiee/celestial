package dev.celestial.world.frozen;

import dev.celestial.data.CelestialData;
import dev.celestial.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
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
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Вмёрзший ангел: глыба льда с фигурой внутри. Разбей её — ангел оттает и останется рядом,
 * а освободителю достанутся Благодать и репутация у ангелов.
 */
public class FrozenAngelBlock extends Block {
	public FrozenAngelBlock(Properties properties) {
		super(properties);
	}

	@Override
	public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
		if (level instanceof ServerLevel server && !player.isCreative()) {
			free(server, pos, player);
		}
		return super.playerWillDestroy(level, pos, state, player);
	}

	private static void free(ServerLevel level, BlockPos pos, Player player) {
		var angel = ModEntities.ANGEL.create(level, EntitySpawnReason.TRIGGERED);
		if (angel != null) {
			angel.snapTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, player.getYRot() + 180, 0);
			angel.setPersistenceRequired();
			level.addFreshEntity(angel);
		}
		level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState()),
			pos.getX() + 0.5, pos.getY() + 1, pos.getZ() + 0.5, 60, 0.5, 0.8, 0.5, 0.1);
		level.sendParticles(dev.celestial.registry.ModParticles.STARLIGHT, pos.getX() + 0.5, pos.getY() + 1.5, pos.getZ() + 0.5, 30, 0.4, 0.6, 0.4, 0.05);
		level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 1.5F, 1.4F);
		if (player instanceof ServerPlayer sp) {
			CelestialData.update(sp, d -> d.withGrace(d.grace() + 1).withReputation(d.reputation() + 2).withCodex("place:frozen_angels"));
			sp.sendSystemMessage(Component.translatable("frozen.celestial.angel_freed"));
		}
	}
}
