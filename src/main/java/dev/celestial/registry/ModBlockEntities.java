package dev.celestial.registry;

import dev.celestial.Celestial;
import dev.celestial.block.SeraphSealBlockEntity;
import java.util.Set;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.block.entity.BlockEntityType;

public final class ModBlockEntities {
	public static final BlockEntityType<SeraphSealBlockEntity> SERAPH_SEAL = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE,
		Celestial.id("seraph_seal"), new BlockEntityType<>(SeraphSealBlockEntity::new, Set.of(ModBlocks.SERAPH_SEAL)));

	private ModBlockEntities() {}

	public static void init() {
	}
}
