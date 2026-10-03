package dev.celestial.starlight;

import dev.celestial.fading.Fading;
import dev.celestial.registry.ModBlockEntities;
import dev.celestial.world.HeavenDimension;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * Запас звёздного света Звездоловки (0–400, флакон стоит 100).
 * Раз в секунду ночью под открытым небом без дождя: +1; в Раю ×2, выше 120 — ещё +1;
 * в Верхнем мире Угасание глушит звёзды (−12% за стадию).
 */
public class StarCollectorBlockEntity extends BlockEntity {
	public static final int MAX = 400;
	public static final int FLASK = 100;
	private float charge;

	public StarCollectorBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.STAR_COLLECTOR, pos, state);
	}

	public int charge() {
		return (int) charge;
	}

	public boolean takeFlask() {
		if (charge < FLASK) {
			return false;
		}
		charge -= FLASK;
		sync();
		return true;
	}

	void serverTick(ServerLevel level, BlockState state) {
		if (level.getGameTime() % 20 != 0 || charge >= MAX) {
			return;
		}
		float gain = rate(level, worldPosition);
		if (gain <= 0) {
			return;
		}
		charge = Math.min(MAX, charge + gain);
		if (level.getRandom().nextInt(3) == 0) {
			level.sendParticles(ParticleTypes.END_ROD, worldPosition.getX() + 0.5, worldPosition.getY() + 6 + level.getRandom().nextInt(4),
				worldPosition.getZ() + 0.5, 1, 0.2, 0, 0.2, 0.0);
		}
		sync();
	}

	/** Сколько света в секунду соберёт Звездоловка в этой точке (0 — днём, под крышей, в дождь, без неба). */
	public static float rate(ServerLevel level, BlockPos pos) {
		boolean heaven = level.dimension() == HeavenDimension.HEAVEN;
		if (!(heaven || level.dimension() == Level.OVERWORLD) || !level.canSeeSky(pos.above()) || level.isRainingAt(pos.above())) {
			return 0;
		}
		if (!Fading.isNight(level.getServer().overworld())) {
			return 0;
		}
		float gain = heaven ? 2.0F : 1.0F;
		if (pos.getY() > 120) {
			gain += 1.0F;
		}
		if (!heaven) {
			gain *= Math.max(0.2F, 1.0F - 0.12F * Fading.stage(level.getServer()));
		}
		return gain;
	}

	private void sync() {
		setChanged();
		int visual = Math.min(4, (int) (charge / FLASK));
		if (level != null && getBlockState().getValue(StarCollectorBlock.CHARGE) != visual) {
			level.setBlock(worldPosition, getBlockState().setValue(StarCollectorBlock.CHARGE, visual), Block.UPDATE_ALL);
		}
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putFloat("Starlight", charge);
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		charge = input.getFloatOr("Starlight", 0.0F);
	}
}
