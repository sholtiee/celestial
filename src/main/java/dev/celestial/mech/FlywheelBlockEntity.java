package dev.celestial.mech;

import dev.celestial.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** Разгон маховика: пока источник крутит его — заряжается; без источника ещё {@link #MOMENTUM} тиков сам крутит сеть в обе стороны оси. */
public class FlywheelBlockEntity extends BlockEntity {
	public static final int MOMENTUM = 200;
	private long chargedUntil;
	private int spin = 1;

	public FlywheelBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.FLYWHEEL, pos, state);
	}

	void charge(long now, int spin) {
		this.chargedUntil = now + MOMENTUM;
		this.spin = spin;
		setChanged();
	}

	public static void serverTick(Level level, BlockPos pos, BlockState state, FlywheelBlockEntity be) {
		if (!(level instanceof ServerLevel server) || level.getGameTime() % Gears.PERIOD != 0) {
			return;
		}
		long now = level.getGameTime();
		if (be.chargedUntil <= now || Gears.primary(level, pos)) {
			return;
		}
		Gears.mark(server, pos, be.spin, false);
		Direction.Axis axis = state.getValue(MechBlock.AXIS);
		for (Direction d : Direction.values()) {
			if (d.getAxis() == axis) {
				Gears.request(server, pos, d, be.spin, false);
			}
		}
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		chargedUntil = input.getLongOr("ChargedUntil", 0L);
		spin = input.getIntOr("Spin", 1);
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putLong("ChargedUntil", chargedUntil);
		output.putInt("Spin", spin);
	}
}
