package dev.celestial.registry;

import dev.celestial.Celestial;
import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

public final class ModCreativeTab {
	private ModCreativeTab() {}

	public static void init() {
		CreativeModeTab tab = FabricCreativeModeTab.builder()
			.title(Component.translatable("itemGroup.celestial"))
			.icon(() -> new ItemStack(ModBlocks.GOLDEN_CLOUD))
			.displayItems((params, output) -> {
				for (Item item : ModItems.ALL) {
					if (item == ModItems.LORE_SCROLL) {  // по свитку на каждый лист-«свиток»; пустой свиток — для команд
						for (var sheet : dev.celestial.lore.Lore.sheets()) {
							if (sheet.src().equals("scroll")) {
								output.accept(dev.celestial.item.LoreScrollItem.of(item, sheet.id()));
							}
						}
						continue;
					}
					output.accept(new ItemStack(item));
				}
			})
			.build();
		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, Celestial.id("main"), tab);
	}
}
