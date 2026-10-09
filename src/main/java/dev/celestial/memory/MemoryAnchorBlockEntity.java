package dev.celestial.memory;

import dev.celestial.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** Какое воспоминание хранит Отпечаток света (`Scene` в NBT шаблона постройки или в /setblock). */
public class MemoryAnchorBlockEntity extends BlockEntity {
	private String scene = "";

	public MemoryAnchorBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.MEMORY_ANCHOR, pos, state);
	}

	public String scene() {
		return scene;
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putString("Scene", scene);
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		scene = input.getStringOr("Scene", "");
	}
}
