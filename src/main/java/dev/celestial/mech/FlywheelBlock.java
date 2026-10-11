package dev.celestial.mech;

import dev.celestial.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import org.jspecify.annotations.Nullable;

/** Маховик: соосная деталь, которая копит разгон и ещё {@link FlywheelBlockEntity#MOMENTUM} тиков крутит сеть без источника. */
public class FlywheelBlock extends MechBlock implements EntityBlock {
	public FlywheelBlock(Properties properties) {
		super(Kind.FLYWHEEL, properties);
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new FlywheelBlockEntity(pos, state);
	}

	@Override
	@SuppressWarnings("unchecked")
	public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		return level.isClientSide() || type != ModBlockEntities.FLYWHEEL ? null
			: (BlockEntityTicker<T>) (BlockEntityTicker<FlywheelBlockEntity>) FlywheelBlockEntity::serverTick;
	}
}
