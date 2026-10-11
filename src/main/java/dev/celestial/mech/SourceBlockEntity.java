package dev.celestial.mech;

import dev.celestial.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** Источник: раз в {@link Gears#PERIOD} тиков, пока работает, раскручивает сеть от выходной грани. */
public class SourceBlockEntity extends BlockEntity {
	private int wound;

	public SourceBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.MECH_SOURCE, pos, state);
	}

	public int wound() {
		return wound;
	}

	void wind() {
		wound = Math.min(SourceBlock.MAX_WIND, wound + SourceBlock.WIND);
		setChanged();
	}

	public static void serverTick(Level level, BlockPos pos, BlockState state, SourceBlockEntity be) {
		if (!(level instanceof ServerLevel server) || !(state.getBlock() instanceof SourceBlock block)) {
			return;
		}
		boolean on;
		if (block.kind() == SourceBlock.Kind.SPRING) {
			if (be.wound > 0) {
				be.wound--;
				if (be.wound % 20 == 0) {
					be.setChanged();
				}
			}
			on = be.wound > 0;
		} else {
			on = SourceBlock.heated(level, pos);
		}
		if (on != state.getValue(SourceBlock.ACTIVE)) {
			level.setBlock(pos, state.setValue(SourceBlock.ACTIVE, on), Block.UPDATE_ALL);
		}
		if (on && level.getGameTime() % Gears.PERIOD == 0) {
			Direction out = state.getValue(SourceBlock.FACING);
			Gears.request(server, pos, out, Gears.spinFor(out), true);
		}
	}

	public static void clientTick(Level level, BlockPos pos, BlockState state, SourceBlockEntity be) {
		if (!state.getValue(SourceBlock.ACTIVE) || !(state.getBlock() instanceof SourceBlock block) || block.kind() != SourceBlock.Kind.ENGINE) {
			return;
		}
		RandomSource r = level.getRandom();
		if (r.nextInt(4) == 0) {  // пар из трубы
			Direction out = state.getValue(SourceBlock.FACING);
			double x = pos.getX() + 0.5 - out.getStepX() * 0.25, z = pos.getZ() + 0.5 - out.getStepZ() * 0.25;
			level.addParticle(ParticleTypes.CLOUD, x, pos.getY() + 1.05, z, (r.nextDouble() - 0.5) * 0.02, 0.06, (r.nextDouble() - 0.5) * 0.02);
		}
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		wound = input.getIntOr("Wound", 0);
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putInt("Wound", wound);
	}
}
