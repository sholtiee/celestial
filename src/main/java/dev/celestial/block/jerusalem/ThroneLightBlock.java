package dev.celestial.block.jerusalem;

import dev.celestial.story.NewJerusalem;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Свет престола посреди Нового Иерусалима. Престол без фигуры — столб света и радуга «видом подобная смарагду» вокруг (Откр. 4:3).
 * ПКМ — вернуться домой, в Верхний мир (к точке появления).
 */
public class ThroneLightBlock extends Block {
	private static final int[] RAINBOW = {0x50E890, 0x7AF0B0, 0xA8F8D0, 0xE8F8A0, 0xF8D870, 0x90E8F8};

	public ThroneLightBlock(Properties properties) {
		super(properties);
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (player instanceof ServerPlayer sp) {
			NewJerusalem.leave(sp);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		double cx = pos.getX() + 0.5, cy = pos.getY() + 0.5, cz = pos.getZ() + 0.5;
		for (int i = 0; i < 3; i++) {
			level.addParticle(ParticleTypes.END_ROD, cx + random.nextGaussian() * 0.2, cy + random.nextDouble() * 2, cz + random.nextGaussian() * 0.2,
				0.0, 0.08 + random.nextDouble() * 0.1, 0.0);
		}
		for (int i = 0; i < 6; i++) {
			double a = random.nextDouble() * Math.PI * 2;
			level.addParticle(new DustParticleOptions(RAINBOW[random.nextInt(RAINBOW.length)], 1.4F),
				cx + Math.cos(a) * 3.5, cy + 2.5 + Math.sin(a * 2) * 0.2, cz + Math.sin(a) * 3.5, 0.0, 0.0, 0.0);
		}
	}
}
