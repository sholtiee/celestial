package dev.celestial.block.lore;

import dev.celestial.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** Какой лист Летописи высечен на скрижали (`Sheet` в NBT шаблона постройки или в /setblock). */
public class LoreTabletBlockEntity extends BlockEntity {
	private String sheet = "";

	public LoreTabletBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.LORE_TABLET, pos, state);
	}

	public String sheet() {
		return sheet;
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putString("Sheet", sheet);
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		sheet = input.getStringOr("Sheet", "");
	}
}
