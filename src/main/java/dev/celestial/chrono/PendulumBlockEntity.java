package dev.celestial.chrono;

import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModParticles;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/** Зона маятника: каждый тик заявляет масштаб хода всем внутри сферы; на клиенте — искры по границе сферы. */
public class PendulumBlockEntity extends BlockEntity {
	public PendulumBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.PENDULUM, pos, state);
	}

	public static void serverTick(Level level, BlockPos pos, BlockState state, PendulumBlockEntity be) {
		if (level instanceof ServerLevel server && state.getBlock() instanceof PendulumBlock block) {
			TimeFlow.claimZone(server, Vec3.atCenterOf(pos), PendulumBlock.RADIUS, block.scale, true);
		}
	}

	public static void clientTick(Level level, BlockPos pos, BlockState state, PendulumBlockEntity be) {
		if (!(state.getBlock() instanceof PendulumBlock block)) {
			return;
		}
		if (level.getGameTime() % Math.max(2, block.period / 2) == 0) {  // тик на каждом крайнем положении
			level.playLocalSound(pos, dev.celestial.registry.ModSounds.CLOCK_TICK, net.minecraft.sounds.SoundSource.BLOCKS, 0.35F,
				block.scale > 1.0F ? 1.4F : 0.75F, false);
		}
		if (level.getGameTime() % 2 != 0) {
			return;
		}
		RandomSource r = level.getRandom();
		boolean fast = block.scale > 1.0F;
		Vec3 c = Vec3.atCenterOf(pos);
		for (int i = 0; i < 3; i++) {
			// точка на сфере; нижнюю половину реже — там обычно земля
			double u = r.nextDouble() * 2 - 1;
			if (u < -0.3 && r.nextBoolean()) {
				u = -u;
			}
			double a = r.nextDouble() * Math.PI * 2;
			double s = Math.sqrt(1 - u * u);
			double x = c.x + Math.cos(a) * s * PendulumBlock.RADIUS;
			double y = c.y + u * PendulumBlock.RADIUS;
			double z = c.z + Math.sin(a) * s * PendulumBlock.RADIUS;
			// касательная скорость: быстрая зона кружит, медленная едва дрейфует
			double v = fast ? 0.06 : 0.008;
			level.addParticle(fast ? ModParticles.CHRONO_HASTE : ModParticles.CHRONO_LAG, x, y, z, -Math.sin(a) * v, 0, Math.cos(a) * v);
		}
	}
}
