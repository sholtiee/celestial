package dev.celestial.registry;

import dev.celestial.Celestial;
import dev.celestial.block.CloudBlock;
import dev.celestial.block.MannaBushBlock;
import dev.celestial.block.RainCloudBlock;
import dev.celestial.world.portal.CelestialPortalBlock;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.util.valueproviders.UniformInt;
import net.minecraft.util.random.WeightedList;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.*;
import net.minecraft.world.level.block.grower.TreeGrower;
import net.minecraft.world.level.block.state.BlockBehaviour.Properties;
import net.minecraft.world.level.block.state.properties.NoteBlockInstrument;
import net.minecraft.world.level.block.state.properties.WoodType;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;

public final class ModBlocks {
	/** Блоки, у которых есть предмет: по этому списку заполняется творческая вкладка. */
	public static final List<Block> WITH_ITEMS = new ArrayList<>();

	public static final ResourceKey<Feature> SKYWOOD_TREE = ResourceKey.create(Registries.FEATURE, Celestial.id("skywood_tree"));
	public static final ResourceKey<Feature> FANCY_SKYWOOD_TREE = ResourceKey.create(Registries.FEATURE, Celestial.id("fancy_skywood_tree"));
	public static final TreeGrower SKYWOOD_GROWER = new TreeGrower("celestial_skywood",
		WeightedList.of(new net.minecraft.util.random.Weighted<>(SKYWOOD_TREE, 4), new net.minecraft.util.random.Weighted<>(FANCY_SKYWOOD_TREE, 1)),
		WeightedList.of(), WeightedList.of(), null);

	// Земля и камень
	public static final Block HEAVEN_DIRT = register("heaven_dirt", Block::new,
		Properties.of().mapColor(MapColor.SAND).strength(0.5F).sound(SoundType.GRAVEL));
	public static final Block GOLDEN_GRASS = register("golden_grass", Block::new,
		Properties.of().mapColor(MapColor.GOLD).strength(0.6F).sound(SoundType.GRASS).randomTicks());
	public static final Block SKYSTONE = register("skystone", Block::new,
		Properties.of().mapColor(MapColor.QUARTZ).instrument(NoteBlockInstrument.BASEDRUM).requiresCorrectToolForDrops().strength(1.5F, 6.0F));
	public static final Block SKYSTONE_BRICKS = register("skystone_bricks", Block::new, Properties.ofFullCopy(SKYSTONE));
	public static final Block SKYSTONE_BRICK_STAIRS = register("skystone_brick_stairs",
		p -> new StairBlock(SKYSTONE_BRICKS.defaultBlockState(), p), Properties.ofFullCopy(SKYSTONE_BRICKS));
	public static final Block SKYSTONE_BRICK_SLAB = register("skystone_brick_slab", SlabBlock::new, Properties.ofFullCopy(SKYSTONE_BRICKS));
	public static final Block SKYSTONE_BRICK_WALL = register("skystone_brick_wall", WallBlock::new, Properties.ofFullCopy(SKYSTONE_BRICKS).forceSolidOn());
	public static final Block RADIANT_STONE = register("radiant_stone", Block::new,
		Properties.of().mapColor(MapColor.GOLD).requiresCorrectToolForDrops().strength(3.0F, 9.0F).lightLevel(s -> 12).sound(SoundType.AMETHYST));

	// Небесное дерево
	public static final Block SKYWOOD_LOG = register("skywood_log", RotatedPillarBlock::new,
		Blocks.logProperties(MapColor.QUARTZ, MapColor.SNOW, SoundType.CHERRY_WOOD));
	public static final Block SKYWOOD_WOOD = register("skywood_wood", RotatedPillarBlock::new,
		Blocks.logProperties(MapColor.SNOW, MapColor.SNOW, SoundType.CHERRY_WOOD));
	public static final Block SKYWOOD_PLANKS = register("skywood_planks", Block::new,
		Properties.of().mapColor(MapColor.QUARTZ).instrument(NoteBlockInstrument.BASS).strength(2.0F, 3.0F).sound(SoundType.CHERRY_WOOD).ignitedByLava());
	public static final Block SKYWOOD_STAIRS = register("skywood_stairs",
		p -> new StairBlock(SKYWOOD_PLANKS.defaultBlockState(), p), Properties.ofFullCopy(SKYWOOD_PLANKS));
	public static final Block SKYWOOD_SLAB = register("skywood_slab", SlabBlock::new, Properties.ofFullCopy(SKYWOOD_PLANKS));
	public static final Block SKYWOOD_FENCE = register("skywood_fence", FenceBlock::new, Properties.ofFullCopy(SKYWOOD_PLANKS).forceSolidOn());
	public static final Block SKYWOOD_FENCE_GATE = register("skywood_fence_gate",
		p -> new FenceGateBlock(WoodType.CHERRY, p), Properties.ofFullCopy(SKYWOOD_PLANKS).forceSolidOn());
	public static final Block SKYWOOD_LEAVES = register("skywood_leaves", p -> new TintedParticleLeavesBlock(0.02F, p),
		Blocks.leavesProperties(SoundType.CHERRY_LEAVES).mapColor(MapColor.GOLD).lightLevel(s -> 3));
	public static final Block SKYWOOD_SAPLING = register("skywood_sapling", p -> new SaplingBlock(SKYWOOD_GROWER, p),
		Properties.of().mapColor(MapColor.GOLD).noCollision().randomTicks().instabreak().sound(SoundType.GRASS).pushReaction(PushReaction.POPPED));

	// Облака
	public static final Block CLOUD = register("cloud", CloudBlock::new,
		Properties.of().mapColor(MapColor.SNOW).strength(0.2F).sound(SoundType.WOOL).noOcclusion().speedFactor(0.8F)
			.isSuffocating(Blocks::never));
	public static final Block GOLDEN_CLOUD = register("golden_cloud", CloudBlock::new,
		Properties.ofFullCopy(CLOUD).mapColor(MapColor.GOLD).bounceRestitution(1.15F));
	public static final Block RAIN_CLOUD = register("rain_cloud", RainCloudBlock::new,
		Properties.ofFullCopy(CLOUD).mapColor(MapColor.COLOR_GRAY).noCollision());

	// Руды и кристаллы
	public static final Block ETHERITE_ORE = register("etherite_ore", p -> new DropExperienceBlock(UniformInt.of(2, 5), p),
		Properties.ofFullCopy(SKYSTONE).strength(3.5F, 6.0F));
	public static final Block STARQUARTZ_ORE = register("starquartz_ore", p -> new DropExperienceBlock(UniformInt.of(3, 7), p),
		Properties.ofFullCopy(SKYSTONE).strength(3.0F, 6.0F).lightLevel(s -> 4));
	public static final Block METEORITE = register("meteorite", Block::new,
		Properties.of().mapColor(MapColor.COLOR_BLACK).requiresCorrectToolForDrops().strength(4.0F, 9.0F).lightLevel(s -> 7).sound(SoundType.ANCIENT_DEBRIS), 1);
	public static final Block TELESCOPE = register("telescope", dev.celestial.fading.TelescopeBlock::new,
		Properties.of().mapColor(MapColor.COLOR_ORANGE).strength(1.5F).noOcclusion().sound(SoundType.COPPER), 1);
	public static final Block ETHERITE_BLOCK = register("etherite_block", Block::new,
		Properties.of().mapColor(MapColor.DIAMOND).requiresCorrectToolForDrops().strength(5.0F, 6.0F).sound(SoundType.METAL));
	public static final Block SKY_CRYSTAL = register("sky_crystal", p -> new AmethystClusterBlock(7.0F, 10.0F, p),
		Properties.of().mapColor(MapColor.COLOR_LIGHT_BLUE).forceSolidOn().noOcclusion().sound(SoundType.AMETHYST_CLUSTER)
			.strength(1.5F).lightLevel(s -> 10).pushReaction(PushReaction.POPPED));

	// Флора Рая 0.2
	public static final Block SKY_LILY = flower("sky_lily", net.minecraft.world.effect.MobEffects.REGENERATION, 0);
	public static final Block SUNBELL = flower("sunbell", net.minecraft.world.effect.MobEffects.SPEED, 7);
	public static final Block CLOUDBLOOM = flower("cloudbloom", net.minecraft.world.effect.MobEffects.SLOW_FALLING, 0);
	public static final Block STARFLOWER = flower("starflower", net.minecraft.world.effect.MobEffects.NIGHT_VISION, 10);
	public static final Block AETHER_ROSE = flower("aether_rose", net.minecraft.world.effect.MobEffects.STRENGTH, 0);
	public static final Block DAWN_POPPY = flower("dawn_poppy", net.minecraft.world.effect.MobEffects.JUMP_BOOST, 0);
	public static final Block GOLDEN_TUFT = register("golden_tuft", TallGrassBlock::new,
		Properties.of().mapColor(MapColor.GOLD).replaceable().noCollision().instabreak().sound(SoundType.GRASS)
			.offsetType(net.minecraft.world.level.block.state.BlockBehaviour.OffsetType.XZ).ignitedByLava().pushReaction(PushReaction.POPPED));
	public static final Block TALL_GOLDEN_GRASS = register("tall_golden_grass", DoublePlantBlock::new,
		Properties.ofFullCopy(GOLDEN_TUFT));
	public static final Block CLOUD_MOSS = register("cloud_moss", CarpetBlock::new,
		Properties.of().mapColor(MapColor.SNOW).strength(0.1F).sound(SoundType.MOSS_CARPET).pushReaction(PushReaction.POPPED));
	public static final Block LUMIVINE = register("lumivine", dev.celestial.block.LumivineBlock::new,
		Properties.of().mapColor(MapColor.COLOR_LIGHT_BLUE).noCollision().instabreak().sound(SoundType.CAVE_VINES)
			.lightLevel(s -> 9).pushReaction(PushReaction.POPPED));
	public static final Block SKY_CRYSTAL_BLOCK = register("sky_crystal_block", Block::new,
		Properties.of().mapColor(MapColor.COLOR_LIGHT_BLUE).strength(1.5F).sound(SoundType.AMETHYST).requiresCorrectToolForDrops().lightLevel(s -> 6));
	// Новые деревья: облачная ива и звёздная сосна (ствол — небесное дерево)
	public static final ResourceKey<Feature> CLOUD_WILLOW_TREE = ResourceKey.create(Registries.FEATURE, Celestial.id("cloud_willow"));
	public static final ResourceKey<Feature> STARPINE_TREE = ResourceKey.create(Registries.FEATURE, Celestial.id("starpine"));
	public static final Block CLOUD_WILLOW_LEAVES = register("cloud_willow_leaves", p -> new TintedParticleLeavesBlock(0.03F, p),
		Blocks.leavesProperties(SoundType.AZALEA_LEAVES).mapColor(MapColor.SNOW));
	public static final Block STARPINE_LEAVES = register("starpine_leaves", p -> new TintedParticleLeavesBlock(0.01F, p),
		Blocks.leavesProperties(SoundType.GRASS).mapColor(MapColor.COLOR_BLUE).lightLevel(s -> 5));
	public static final Block CLOUD_WILLOW_SAPLING = register("cloud_willow_sapling",
		p -> new SaplingBlock(new TreeGrower("celestial_cloud_willow", WeightedList.of(CLOUD_WILLOW_TREE),
			WeightedList.of(), WeightedList.of(), null), p), Properties.ofFullCopy(SKYWOOD_SAPLING));
	public static final Block STARPINE_SAPLING = register("starpine_sapling",
		p -> new SaplingBlock(new TreeGrower("celestial_starpine", WeightedList.of(STARPINE_TREE),
			WeightedList.of(), WeightedList.of(), null), p), Properties.ofFullCopy(SKYWOOD_SAPLING));

	// Растения (у куста предмет — сама манна, регистрируется в ModItems)
	public static final Block MANNA_BUSH = registerNoItem("manna_bush", MannaBushBlock::new,
		Properties.of().mapColor(MapColor.PLANT).randomTicks().noCollision().sound(SoundType.SWEET_BERRY_BUSH).pushReaction(PushReaction.POPPED).lightLevel(s -> 4));

	// Портал в Рай (без предмета: появляется при активации рамки Сердцем Пустоты)
	public static final Block HEAVEN_PORTAL = registerNoItem("heaven_portal", p -> new CelestialPortalBlock(() -> dev.celestial.world.portal.PortalTypes.HEAVEN, p),
		Properties.of().noCollision().strength(-1.0F).sound(SoundType.GLASS).lightLevel(s -> 13).pushReaction(PushReaction.IMMOVEABLE).noLootTable());

	// Светотехника
	public static final Block SUN_LENS = register("sun_lens", p -> new dev.celestial.block.light.BeamSourceBlock(
		dev.celestial.block.light.BeamSourceBlock.Kind.SUN_LENS, p), Properties.of().mapColor(MapColor.GOLD).strength(2.0F).sound(SoundType.AMETHYST)
			.lightLevel(s -> s.getValue(dev.celestial.block.light.BeamSourceBlock.ACTIVE) ? 12 : 3).noOcclusion());
	public static final Block BEAM_LANTERN = register("beam_lantern", p -> new dev.celestial.block.light.BeamSourceBlock(
		dev.celestial.block.light.BeamSourceBlock.Kind.LANTERN, p), Properties.ofFullCopy(SUN_LENS));
	public static final Block BEAM_MIRROR = register("beam_mirror", dev.celestial.block.light.BeamMirrorBlock::new,
		Properties.of().mapColor(MapColor.QUARTZ).strength(1.5F).sound(SoundType.GLASS).noOcclusion());
	public static final Block BEAM_PRISM = register("beam_prism", dev.celestial.block.light.BeamPrismBlock::new,
		Properties.of().mapColor(MapColor.DIAMOND).strength(1.5F).sound(SoundType.AMETHYST).noOcclusion().lightLevel(s -> 5));
	public static final Block RED_FILTER = register("red_filter", p -> new dev.celestial.block.light.BeamFilterBlock(dev.celestial.light.LightColor.RED, p),
		Properties.of().mapColor(MapColor.COLOR_RED).strength(0.5F).sound(SoundType.GLASS).noOcclusion());
	public static final Block GREEN_FILTER = register("green_filter", p -> new dev.celestial.block.light.BeamFilterBlock(dev.celestial.light.LightColor.GREEN, p),
		Properties.of().mapColor(MapColor.COLOR_GREEN).strength(0.5F).sound(SoundType.GLASS).noOcclusion());
	public static final Block BLUE_FILTER = register("blue_filter", p -> new dev.celestial.block.light.BeamFilterBlock(dev.celestial.light.LightColor.BLUE, p),
		Properties.of().mapColor(MapColor.COLOR_BLUE).strength(0.5F).sound(SoundType.GLASS).noOcclusion());
	public static final Block PERISCOPE = register("periscope", dev.celestial.block.light.PeriscopeBlock::new,
		Properties.of().mapColor(MapColor.QUARTZ).strength(1.5F).sound(SoundType.GLASS).noOcclusion());
	public static final Block LIGHT_RECEIVER = register("light_receiver", dev.celestial.block.light.LightReceiverBlock::new,
		Properties.of().mapColor(MapColor.GOLD).strength(2.0F).sound(SoundType.METAL)
			.lightLevel(s -> s.getValue(dev.celestial.block.light.LightReceiverBlock.POWERED) ? 10 : 0));

	// Машины
	public static final Block CLOUD_LIFT = register("cloud_lift", dev.celestial.block.machine.CloudLiftBlock::new,
		Properties.of().mapColor(MapColor.SNOW).strength(1.0F).sound(SoundType.WOOL)
			.noOcclusion()  // текстура полупрозрачная: без этого соседние грани отсекаются и сквозь лифт видна пустота
			.lightLevel(s -> s.getValue(dev.celestial.block.machine.CloudLiftBlock.LIT) ? 8 : 0));
	public static final Block CELESTIAL_FORGE = register("celestial_forge", dev.celestial.block.machine.CelestialForgeBlock::new,
		Properties.of().mapColor(MapColor.GOLD).strength(5.0F, 1200.0F).requiresCorrectToolForDrops().sound(SoundType.ANVIL).lightLevel(s -> 6));
	public static final Block INFUSION_ALTAR = register("infusion_altar", dev.celestial.block.machine.InfusionAltarBlock::new,
		Properties.of().mapColor(MapColor.COLOR_LIGHT_BLUE).strength(4.0F, 1200.0F).requiresCorrectToolForDrops().sound(SoundType.AMETHYST).lightLevel(s -> 8));
	public static final Block SKY_BEACON = register("sky_beacon", dev.celestial.block.machine.SkyBeaconBlock::new,
		Properties.of().mapColor(MapColor.GOLD).strength(3.0F, 1200.0F).requiresCorrectToolForDrops().sound(SoundType.AMETHYST).lightLevel(s -> 15));

	public static final Block QUEST_BOARD = register("quest_board", dev.celestial.quest.QuestBoardBlock::new,
		Properties.of().mapColor(MapColor.WOOD).strength(2.0F).sound(SoundType.CHERRY_WOOD).noOcclusion());

	// Испытания
	public static final Block TRIAL_CONTROLLER = register("trial_crystal", dev.celestial.trial.TrialControllerBlock::new,
		Properties.of().mapColor(MapColor.GOLD).strength(-1.0F, 3600000.0F).noLootTable().sound(SoundType.AMETHYST).noOcclusion()
			.lightLevel(s -> s.getValue(dev.celestial.trial.TrialControllerBlock.STATE) == dev.celestial.trial.TrialControllerBlock.TrialState.IDLE ? 6 : 15));
	public static final Block TRIAL_GOAL = register("trial_goal", dev.celestial.trial.TrialGoalBlock::new,
		Properties.of().mapColor(MapColor.DIAMOND).strength(-1.0F, 3600000.0F).noLootTable().sound(SoundType.AMETHYST).lightLevel(s -> 12));
	public static final Block VANISHING_CLOUD = register("vanishing_cloud", dev.celestial.trial.VanishingCloudBlock::new,
		Properties.of().mapColor(MapColor.SNOW).strength(-1.0F, 3600000.0F).noLootTable().sound(SoundType.WOOL).noOcclusion());

	// Загадки
	public static final Block SEALED_DOOR = register("sealed_door", dev.celestial.block.puzzle.SealedDoorBlock::new,
		Properties.of().mapColor(MapColor.GOLD).strength(-1.0F, 3600000.0F).noLootTable().sound(SoundType.AMETHYST).lightLevel(s -> 6));
	public static final Block SKY_BELL = register("sky_bell", dev.celestial.block.puzzle.SkyBellBlock::new,
		Properties.of().mapColor(MapColor.GOLD).strength(2.0F).sound(SoundType.ANVIL).noOcclusion());
	public static final Block BELL_ALTAR = register("bell_altar", dev.celestial.block.puzzle.BellAltarBlock::new,
		Properties.of().mapColor(MapColor.QUARTZ).strength(-1.0F, 3600000.0F).noLootTable().sound(SoundType.STONE));
	public static final Block RUNE_PEDESTAL = register("rune_pedestal", dev.celestial.block.puzzle.RunePedestalBlock::new,
		Properties.of().mapColor(MapColor.QUARTZ).strength(-1.0F, 3600000.0F).noLootTable().sound(SoundType.STONE)
			.lightLevel(s -> s.getValue(dev.celestial.block.puzzle.RunePedestalBlock.SOLVED) ? 12 : 4));
	public static final Block STAR_TILE = register("star_tile", dev.celestial.block.puzzle.StarTileBlock::new,
		Properties.of().mapColor(MapColor.COLOR_BLUE).strength(-1.0F, 3600000.0F).noLootTable().sound(SoundType.AMETHYST)
			.lightLevel(s -> s.getValue(dev.celestial.block.puzzle.StarTileBlock.LIT) ? 10 : 2));

	// Сюжетные блоки Цитадели
	public static final Block SERAPH_SEAL = register("seraph_seal", dev.celestial.block.SeraphSealBlock::new,
		Properties.of().mapColor(MapColor.GOLD).strength(-1.0F, 3600000.0F).noLootTable().lightLevel(s -> 15).sound(SoundType.AMETHYST));
	public static final Block CELESTIAL_ALTAR = register("celestial_altar", dev.celestial.block.CelestialAltarBlock::new,
		Properties.of().mapColor(MapColor.QUARTZ).strength(-1.0F, 3600000.0F).noLootTable().lightLevel(s -> 10).noOcclusion().sound(SoundType.STONE));

	// ---------------------------------------------------------------- Бездна (волна 0.3)
	public static final Block ABYSS_STONE = register("abyss_stone", Block::new,
		Properties.of().mapColor(MapColor.COLOR_BLACK).requiresCorrectToolForDrops().strength(2.0F, 6.0F).sound(SoundType.DEEPSLATE));
	public static final Block ABYSS_BRICKS = register("abyss_bricks", Block::new, Properties.ofFullCopy(ABYSS_STONE).sound(SoundType.DEEPSLATE_BRICKS));
	public static final Block GLOOM_MOSS = register("gloom_moss", Block::new,
		Properties.of().mapColor(MapColor.COLOR_CYAN).requiresCorrectToolForDrops().strength(1.5F, 6.0F).sound(SoundType.MOSS).lightLevel(s -> 2));
	public static final Block GLOWSHROOM = register("glowshroom",
		p -> new net.minecraft.world.level.block.MushroomBlock(dev.celestial.world.dim.AbyssFeatures.HUGE_GLOWSHROOM, p),
		Properties.of().mapColor(MapColor.COLOR_CYAN).noCollision().randomTicks().instabreak().sound(SoundType.GRASS).lightLevel(s -> 10)
			.offsetType(net.minecraft.world.level.block.state.BlockBehaviour.OffsetType.XZ).pushReaction(PushReaction.POPPED), 1);
	public static final Block GLOWSHROOM_CAP = register("glowshroom_cap", net.minecraft.world.level.block.HugeMushroomBlock::new,
		Properties.of().mapColor(MapColor.COLOR_CYAN).strength(0.2F).sound(SoundType.WOOD).lightLevel(s -> 13));
	public static final Block GLOWSHROOM_STEM = register("glowshroom_stem", net.minecraft.world.level.block.HugeMushroomBlock::new,
		Properties.of().mapColor(MapColor.WOOL).strength(0.2F).sound(SoundType.WOOD).lightLevel(s -> 4));
	public static final Block SHADOW_CRYSTAL = register("shadow_crystal", p -> new AmethystClusterBlock(7.0F, 3.0F, p),
		Properties.of().mapColor(MapColor.COLOR_PURPLE).forceSolidOn().noOcclusion().sound(SoundType.AMETHYST_CLUSTER)
			.strength(1.5F).lightLevel(s -> 6).pushReaction(PushReaction.POPPED));
	public static final Block ABYSSAL_OBSIDIAN_ORE = register("abyssal_obsidian_ore", p -> new DropExperienceBlock(UniformInt.of(4, 8), p),
		Properties.of().mapColor(MapColor.COLOR_BLACK).requiresCorrectToolForDrops().strength(25.0F, 1200.0F).sound(SoundType.DEEPSLATE));

	public static final Block STAR_COLLECTOR = register("star_collector", dev.celestial.starlight.StarCollectorBlock::new,
		Properties.of().mapColor(MapColor.QUARTZ).strength(2.0F).noOcclusion().sound(SoundType.STONE)
			.lightLevel(s -> s.getValue(dev.celestial.starlight.StarCollectorBlock.CHARGE) * 3), 2);
	public static final Block STAR_BASIN = register("star_basin", dev.celestial.starlight.StarBasinBlock::new,
		Properties.of().mapColor(MapColor.QUARTZ).strength(2.0F).noOcclusion().sound(SoundType.STONE)
			.lightLevel(s -> s.getValue(dev.celestial.starlight.StarBasinBlock.LEVEL) * 4), 2);
	public static final Block WARD = register("ward", dev.celestial.starlight.WardBlock::new,
		Properties.of().mapColor(MapColor.QUARTZ).strength(3.0F).noOcclusion().sound(SoundType.STONE)
			.lightLevel(s -> s.getValue(dev.celestial.starlight.WardBlock.LIT) ? 15 : s.getValue(dev.celestial.starlight.WardBlock.CRYSTAL) ? 5 : 0), 2);
	public static final Block BRAZIER = register("brazier", dev.celestial.boss.BrazierBlock::new,
		Properties.of().mapColor(MapColor.COLOR_BLACK).strength(3.0F, 9.0F).noOcclusion().sound(SoundType.DEEPSLATE_BRICKS)
			.lightLevel(s -> s.getValue(dev.celestial.boss.BrazierBlock.LIT) ? 15 : 0), 1);
	public static final Block DEVOURER_SEAL = register("devourer_seal", dev.celestial.boss.DevourerSealBlock::new,
		Properties.of().mapColor(MapColor.COLOR_PURPLE).strength(-1.0F, 3600000.0F).noLootTable().lightLevel(s -> 6).sound(SoundType.DEEPSLATE));
	// ---------------------------------------------------------------- Ледяные Чертоги (волна 0.4)
	public static final Block FROST_STONE = register("frost_stone", Block::new,
		Properties.of().mapColor(MapColor.ICE).requiresCorrectToolForDrops().strength(2.0F, 6.0F).sound(SoundType.DEEPSLATE).friction(0.9F));
	public static final Block FROST_STONE_BRICKS = register("frost_stone_bricks", Block::new,
		Properties.ofFullCopy(FROST_STONE).sound(SoundType.DEEPSLATE_BRICKS).friction(0.6F));
	public static final Block AURORA_CRYSTAL = register("aurora_crystal", p -> new AmethystClusterBlock(7.0F, 3.0F, p),
		Properties.of().mapColor(MapColor.COLOR_LIGHT_GREEN).forceSolidOn().noOcclusion().sound(SoundType.AMETHYST_CLUSTER)
			.strength(1.5F).lightLevel(s -> 11).pushReaction(PushReaction.POPPED));
	public static final Block FROST_ORE = register("frost_ore", p -> new DropExperienceBlock(UniformInt.of(3, 6), p),
		Properties.ofFullCopy(FROST_STONE).strength(4.0F, 6.0F).sound(SoundType.DEEPSLATE));
	public static final Block FROZEN_ANGEL = register("frozen_angel", dev.celestial.world.frozen.FrozenAngelBlock::new,
		Properties.of().mapColor(MapColor.ICE).strength(2.5F).noOcclusion().sound(SoundType.GLASS).lightLevel(s -> 6).friction(0.98F), 1);
	public static final Block FROZEN_PORTAL = registerNoItem("frozen_portal",
		p -> new dev.celestial.world.portal.CelestialPortalBlock(() -> dev.celestial.world.portal.PortalTypes.FROZEN, p),
		Properties.of().noCollision().strength(-1.0F).sound(SoundType.GLASS).lightLevel(s -> 11).pushReaction(PushReaction.IMMOVEABLE).noLootTable());
	public static final Block ABYSS_RIFT = registerNoItem("abyss_rift", dev.celestial.world.abyss.AbyssRiftBlock::new,
		Properties.of().mapColor(MapColor.COLOR_BLACK).noCollision().lightLevel(s -> 8).strength(-1.0F, 3600000.0F).noLootTable()
			.pushReaction(PushReaction.IMMOVEABLE));

	private ModBlocks() {}

	private static Block flower(String name, net.minecraft.core.Holder<net.minecraft.world.effect.MobEffect> effect, int light) {
		return register(name, p -> new FlowerBlock(effect, 5.0F, p), Properties.of().mapColor(MapColor.PLANT).noCollision().instabreak()
			.sound(SoundType.GRASS).offsetType(net.minecraft.world.level.block.state.BlockBehaviour.OffsetType.XZ)
			.pushReaction(PushReaction.POPPED).lightLevel(s -> light));
	}

	private static Block registerNoItem(String name, Function<Properties, Block> factory, Properties properties) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, Celestial.id(name));
		return Blocks.register(key, factory, properties);
	}

	/** Блок с подсказкой в описании предмета (строки block.celestial.<имя>.lore1..N). */
	private static Block register(String name, Function<Properties, Block> factory, Properties properties, int loreLines) {
		Block block = registerNoItem(name, factory, properties);
		java.util.List<net.minecraft.network.chat.Component> lines = new java.util.ArrayList<>();
		for (int i = 1; i <= loreLines; i++) {
			lines.add(net.minecraft.network.chat.Component.translatable("block.celestial." + name + ".lore" + i).withStyle(net.minecraft.ChatFormatting.GRAY));
		}
		ModItems.register(name, p -> new BlockItem(block, p), new Item.Properties().useBlockDescriptionPrefix()
			.component(net.minecraft.core.component.DataComponents.LORE, new net.minecraft.world.item.component.ItemLore(lines)));
		WITH_ITEMS.add(block);
		return block;
	}

	private static Block register(String name, Function<Properties, Block> factory, Properties properties) {
		Block block = registerNoItem(name, factory, properties);
		ModItems.register(name, p -> new BlockItem(block, p), new Item.Properties().useBlockDescriptionPrefix());
		WITH_ITEMS.add(block);
		return block;
	}

	public static void init() {
		Celestial.LOGGER.debug("Блоки Celestial: {}", WITH_ITEMS.size());
	}
}
