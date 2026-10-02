package dev.celestial.registry;

import dev.celestial.Celestial;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.ToolMaterial;
import net.minecraft.world.item.equipment.ArmorMaterial;
import net.minecraft.world.item.equipment.ArmorType;
import net.minecraft.world.item.equipment.EquipmentAsset;
import net.minecraft.world.item.equipment.EquipmentAssets;

public final class ModItems {
	/** Все предметы мода в порядке регистрации (для творческой вкладки). */
	public static final List<Item> ALL = new ArrayList<>();

	public static final TagKey<Item> ETHERITE_TOOL_MATERIALS = TagKey.create(Registries.ITEM, Celestial.id("etherite_tool_materials"));
	public static final TagKey<Item> REPAIRS_ETHERITE_ARMOR = TagKey.create(Registries.ITEM, Celestial.id("repairs_etherite_armor"));
	public static final ResourceKey<EquipmentAsset> ETHERITE_ASSET = ResourceKey.create(EquipmentAssets.ROOT_ID, Celestial.id("etherite"));

	/** Эфирит: прочнее и быстрее алмаза, но слабее незерита по урону. */
	public static final ToolMaterial ETHERITE_TOOL = new ToolMaterial(BlockTags.INCORRECT_FOR_DIAMOND_TOOL, 1800, 9.0F, 3.5F, 18, ETHERITE_TOOL_MATERIALS);
	public static final ArmorMaterial ETHERITE_ARMOR = new ArmorMaterial(35,
		Map.of(ArmorType.BOOTS, 3, ArmorType.LEGGINGS, 6, ArmorType.CHESTPLATE, 8, ArmorType.HELMET, 3, ArmorType.BODY, 13),
		18, SoundEvents.ARMOR_EQUIP_DIAMOND, 2.5F, 0.05F, REPAIRS_ETHERITE_ARMOR, ETHERITE_ASSET);

	// Материалы
	public static final Item RAW_ETHERITE = register("raw_etherite", Item::new, new Item.Properties());
	public static final Item ETHERITE_INGOT = register("etherite_ingot", Item::new, new Item.Properties());
	public static final Item STARQUARTZ = register("starquartz", Item::new, new Item.Properties());
	public static final Item CLOUD_FLUFF = register("cloud_fluff", Item::new, new Item.Properties());
	public static final Item MANNA_BERRIES = register("manna_berries", p -> new BlockItem(ModBlocks.MANNA_BUSH, p),
		new Item.Properties().food(new FoodProperties.Builder().nutrition(4).saturationModifier(0.6F).build()));

	// Инструменты из эфирита
	public static final Item ETHERITE_SWORD = register("etherite_sword", Item::new, new Item.Properties().sword(ETHERITE_TOOL, 3.0F, -2.4F));
	public static final Item ETHERITE_PICKAXE = register("etherite_pickaxe", Item::new, new Item.Properties().pickaxe(ETHERITE_TOOL, 1.0F, -2.8F));
	public static final Item ETHERITE_AXE = register("etherite_axe", Item::new, new Item.Properties().axe(ETHERITE_TOOL, 5.0F, -3.0F));
	public static final Item ETHERITE_SHOVEL = register("etherite_shovel", Item::new, new Item.Properties().shovel(ETHERITE_TOOL, 1.5F, -3.0F));
	public static final Item ETHERITE_HOE = register("etherite_hoe", Item::new, new Item.Properties().hoe(ETHERITE_TOOL, -3.0F, 0.0F));

	// Броня из эфирита
	public static final Item ETHERITE_HELMET = register("etherite_helmet", Item::new, new Item.Properties().humanoidArmor(ETHERITE_ARMOR, ArmorType.HELMET));
	public static final Item ETHERITE_CHESTPLATE = register("etherite_chestplate", Item::new, new Item.Properties().humanoidArmor(ETHERITE_ARMOR, ArmorType.CHESTPLATE));
	public static final Item ETHERITE_LEGGINGS = register("etherite_leggings", Item::new, new Item.Properties().humanoidArmor(ETHERITE_ARMOR, ArmorType.LEGGINGS));
	public static final Item ETHERITE_BOOTS = register("etherite_boots", Item::new, new Item.Properties().humanoidArmor(ETHERITE_ARMOR, ArmorType.BOOTS));

	// Сюжетные предметы
	public static final Item FLAME_SHARD = register("flame_shard", Item::new, new Item.Properties().rarity(Rarity.RARE).fireResistant().stacksTo(16));
	public static final Item VOID_HEART = register("void_heart", dev.celestial.item.VoidHeartItem::new, new Item.Properties().rarity(Rarity.EPIC).stacksTo(1));

	private ModItems() {}

	public static Item register(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, Celestial.id(name));
		Item item = factory.apply(properties.setId(key));
		if (item instanceof BlockItem blockItem) {
			blockItem.registerBlocks(Item.BY_BLOCK, item);
		}
		Registry.register(BuiltInRegistries.ITEM, key, item);
		ALL.add(item);
		return item;
	}

	public static void init() {
	}
}
