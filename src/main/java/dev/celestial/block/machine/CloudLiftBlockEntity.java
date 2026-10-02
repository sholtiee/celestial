package dev.celestial.block.machine;

import dev.celestial.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

public class CloudLiftBlockEntity extends BlockEntity {
	public CloudLiftBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.CLOUD_LIFT, pos, state);
	}
}
