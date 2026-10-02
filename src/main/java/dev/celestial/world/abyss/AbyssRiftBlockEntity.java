package dev.celestial.world.abyss;

import dev.celestial.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.TheEndPortalBlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Разлом рисуется ванильным «звёздным» рендером портала Энда — поэтому наследуем его сущность блока. */
public class AbyssRiftBlockEntity extends TheEndPortalBlockEntity {
	public AbyssRiftBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.ABYSS_RIFT, pos, state);
	}
}
