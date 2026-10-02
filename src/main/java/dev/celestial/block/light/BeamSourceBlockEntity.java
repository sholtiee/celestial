package dev.celestial.block.light;

import dev.celestial.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Нужен только ради тикера источника (работает и в постройках, сгенерированных миром). */
public class BeamSourceBlockEntity extends BlockEntity {
	public BeamSourceBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.BEAM_SOURCE, pos, state);
	}
}
