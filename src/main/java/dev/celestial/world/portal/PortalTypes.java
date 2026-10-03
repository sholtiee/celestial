package dev.celestial.world.portal;

import dev.celestial.registry.ModBlocks;
import dev.celestial.registry.ModItems;
import dev.celestial.world.HeavenDimension;
import java.util.List;
import net.minecraft.world.level.Level;

/** Все порталы мода. Новое измерение = новая запись здесь + блок завесы в ModBlocks. */
public final class PortalTypes {
	public static final PortalType HEAVEN = new PortalType("heaven",
		() -> ModBlocks.RADIANT_STONE, () -> ModBlocks.HEAVEN_PORTAL, () -> ModItems.VOID_HEART,
		Level.OVERWORLD, HeavenDimension.HEAVEN,
		s -> s.is(ModBlocks.GOLDEN_GRASS) || s.is(ModBlocks.SKYSTONE),
		() -> ModBlocks.SKYSTONE_BRICKS.defaultBlockState(), 124);

	/** Ледяные Чертоги: рамка из кирпичей морозного камня, зажигается Тёмным Ядром (награда Акта II). */
	public static final PortalType FROZEN = new PortalType("frozen",
		() -> ModBlocks.FROST_STONE_BRICKS, () -> ModBlocks.FROZEN_PORTAL, () -> ModItems.DARK_CORE,
		Level.OVERWORLD, dev.celestial.world.dim.AbyssFeatures.FROZEN_HALLS,
		s -> s.is(net.minecraft.world.level.block.Blocks.SNOW_BLOCK) || s.is(net.minecraft.world.level.block.Blocks.PACKED_ICE) || s.is(ModBlocks.FROST_STONE),
		() -> ModBlocks.FROST_STONE_BRICKS.defaultBlockState(), 90);

	public static final List<PortalType> ALL = List.of(HEAVEN, FROZEN);

	private PortalTypes() {}
}
