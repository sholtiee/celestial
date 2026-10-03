package dev.celestial.starlight;

import dev.celestial.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** Топливо Оберега в тиках: каждый флакон — 5 минут, запас до 20 минут. */
public class WardBlockEntity extends BlockEntity {
	public static final int PER_FLASK = 20 * 60 * 5;
	public static final int MAX_FUEL = PER_FLASK * 4;
	private int fuel;

	public WardBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.WARD, pos, state);
	}

	public int fuel() {
		return fuel;
	}

	public boolean addFlask() {
		if (fuel + PER_FLASK > MAX_FUEL) {
			return false;
		}
		fuel += PER_FLASK;
		setChanged();
		return true;
	}

	void serverTick(ServerLevel level, BlockState state) {
		boolean active = state.getValue(WardBlock.CRYSTAL) && fuel > 0;
		if (active) {
			fuel--;
			if (fuel % 200 == 0) {
				setChanged();
			}
			if (level.getGameTime() % 10 == 0) {
				level.sendParticles(dev.celestial.registry.ModParticles.STARLIGHT, worldPosition.getX() + 0.5, worldPosition.getY() + 1.6, worldPosition.getZ() + 0.5,
					2, 0.15, 0.3, 0.15, 0.02);
			}
			if (level.getGameTime() % 40 == 0) {  // граница защиты — кольцо искр
				for (int i = 0; i < 24; i++) {
					double a = i * Math.PI / 12;
					level.sendParticles(ParticleTypes.WAX_OFF, worldPosition.getX() + 0.5 + Math.cos(a) * Wards.RADIUS,
						worldPosition.getY() + 1, worldPosition.getZ() + 0.5 + Math.sin(a) * Wards.RADIUS, 1, 0, 0.3, 0, 0);
				}
			}
		}
		if (state.getValue(WardBlock.LIT) != active) {
			level.setBlock(worldPosition, state.setValue(WardBlock.LIT, active), Block.UPDATE_ALL);
		}
		Wards.set(level, worldPosition, active);
	}

	@Override
	public void setRemoved() {
		if (level != null) {
			Wards.set(level, worldPosition, false);
		}
		super.setRemoved();
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putInt("Fuel", fuel);
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		fuel = input.getIntOr("Fuel", 0);
	}
}
