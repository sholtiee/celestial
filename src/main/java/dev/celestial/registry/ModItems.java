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
import net.minecraft.world.item.equipment.Equippable;
import net.minecraft.core.component.DataComponents;
import net.minecraft.util.Unit;
import net.minecraft.world.entity.EquipmentSlot;

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
	public static final Item FLAME_SHARD = register("flame_shard", Item::new, lore(new Item.Properties().rarity(Rarity.RARE).fireResistant().stacksTo(16), "flame_shard", 1));
	public static final Item WANDERER_JOURNAL = register("wanderer_journal", dev.celestial.item.WandererJournalItem::new,
		lore(new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON), "wanderer_journal", 1));
	public static final Item LIGHT_SHARD = register("light_shard", Item::new, lore(new Item.Properties().rarity(Rarity.EPIC).stacksTo(16).fireResistant(), "light_shard", 1));
	public static final Item VOID_HEART = register("void_heart", dev.celestial.item.VoidHeartItem::new, lore(new Item.Properties().rarity(Rarity.EPIC).stacksTo(1), "void_heart", 2));

	// Крылья Серафима: как элитры, но во время полёта можно взмахивать (см. SeraphWingsHandler)
	public static final ResourceKey<EquipmentAsset> SERAPH_WINGS_ASSET = ResourceKey.create(EquipmentAssets.ROOT_ID, Celestial.id("seraph_wings"));
	public static final Item SERAPH_WINGS = register("seraph_wings", Item::new, lore(new Item.Properties()
		.durability(640).rarity(Rarity.EPIC)
		.component(DataComponents.GLIDER, Unit.INSTANCE)
		.component(DataComponents.EQUIPPABLE, Equippable.builder(EquipmentSlot.CHEST).setEquipSound(SoundEvents.ARMOR_EQUIP_ELYTRA)
			.setAsset(SERAPH_WINGS_ASSET).setDamageOnHurt(false).build())
		.repairable(STARQUARTZ), "seraph_wings", 2));

	public static final Item SERAPH_FEATHER = register("seraph_feather", Item::new, new Item.Properties().rarity(Rarity.UNCOMMON));
	public static final ResourceKey<net.minecraft.world.item.JukeboxSong> HEAVENLY_CHOIR_SONG =
		ResourceKey.create(Registries.JUKEBOX_SONG, Celestial.id("heavenly_choir"));
	public static final Item MUSIC_DISC_HEAVENLY_CHOIR = register("music_disc_heavenly_choir", Item::new,
		new Item.Properties().stacksTo(1).rarity(Rarity.RARE).jukeboxPlayable(HEAVENLY_CHOIR_SONG));
	// Нимб: носится на голове, даёт регенерацию и ночное зрение (EquipmentEffects)
	public static final Item HALO = register("halo", Item::new, lore(new Item.Properties().stacksTo(1).rarity(Rarity.EPIC)
		.component(DataComponents.EQUIPPABLE, Equippable.builder(EquipmentSlot.HEAD).setEquipSound(SoundEvents.ARMOR_EQUIP_GOLD).build()), "halo", 1));
	// Облачный парашют: раскрывается сам при опасном падении (EquipmentEffects)
	public static final Item CLOUD_PARACHUTE = register("cloud_parachute", Item::new, lore(new Item.Properties().stacksTo(16), "cloud_parachute", 1));
	public static final Item STARBOW = register("starbow", dev.celestial.item.StarbowItem::new,
		lore(new Item.Properties().durability(520).rarity(Rarity.RARE).enchantable(1).repairable(STARQUARTZ), "starbow", 1));
	public static final Item LIGHT_SPEAR = register("light_spear", dev.celestial.item.LightSpearItem::new,
		lore(new Item.Properties().durability(300).rarity(Rarity.RARE).enchantable(1).repairable(STARQUARTZ), "light_spear", 1));

	// Ключи от хранилищ в руинах (сундуки заперты на предмет-ключ в руке)
	public static final Item BRONZE_KEY = register("bronze_key", Item::new, lore(new Item.Properties().stacksTo(16).rarity(Rarity.UNCOMMON), "bronze_key", 1));
	public static final Item SILVER_KEY = register("silver_key", Item::new, lore(new Item.Properties().stacksTo(16).rarity(Rarity.RARE), "silver_key", 1));
	public static final Item GOLDEN_KEY = register("golden_key", Item::new, lore(new Item.Properties().stacksTo(16).rarity(Rarity.EPIC), "golden_key", 1));

	private ModItems() {}

	/** Описание под названием предмета: строки item.celestial.<имя>.lore1..N из файлов перевода. */
	private static Item.Properties lore(Item.Properties properties, String name, int lines) {
		java.util.List<net.minecraft.network.chat.Component> list = new java.util.ArrayList<>();
		for (int i = 1; i <= lines; i++) {
			list.add(net.minecraft.network.chat.Component.translatable("item.celestial." + name + ".lore" + i)
				.withStyle(net.minecraft.ChatFormatting.GRAY));
		}
		return properties.component(DataComponents.LORE, new net.minecraft.world.item.component.ItemLore(list));
	}

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
