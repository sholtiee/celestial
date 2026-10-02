package dev.celestial.registry;

import dev.celestial.Celestial;
import dev.celestial.entity.Angel;
import dev.celestial.entity.Cherub;
import dev.celestial.entity.CloudJelly;
import dev.celestial.entity.GoldenRam;
import dev.celestial.entity.Mimic;
import dev.celestial.entity.SkyRay;
import dev.celestial.entity.StormElemental;
import dev.celestial.entity.CloudWhale;
import dev.celestial.entity.FallenGuardian;
import dev.celestial.entity.FallenSeraph;
import dev.celestial.entity.LightWisp;
import dev.celestial.entity.LightSpear;
import dev.celestial.entity.Pegasus;
import dev.celestial.entity.StarArrow;
import dev.celestial.entity.StormSpirit;
import dev.celestial.entity.WingedSerpent;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.SpawnPlacementTypes;
import net.minecraft.world.entity.SpawnPlacements;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.levelgen.Heightmap;

public final class ModEntities {
	public static final EntityType<FallenGuardian> FALLEN_GUARDIAN = register("fallen_guardian",
		EntityType.Builder.of(FallenGuardian::new, MobCategory.MONSTER).sized(0.6F, 1.95F).eyeHeight(1.74F).clientTrackingRange(8));
	public static final EntityType<StormSpirit> STORM_SPIRIT = register("storm_spirit",
		EntityType.Builder.of(StormSpirit::new, MobCategory.MONSTER).fireImmune().sized(0.6F, 1.8F).clientTrackingRange(8));
	public static final EntityType<WingedSerpent> WINGED_SERPENT = register("winged_serpent",
		EntityType.Builder.of(WingedSerpent::new, MobCategory.MONSTER).sized(0.9F, 0.5F).eyeHeight(0.175F).clientTrackingRange(8));
	public static final EntityType<CloudWhale> CLOUD_WHALE = register("cloud_whale",
		EntityType.Builder.of(CloudWhale::new, MobCategory.CREATURE).sized(3.5F, 2.2F).eyeHeight(1.2F).clientTrackingRange(12));
	public static final EntityType<LightWisp> LIGHT_WISP = register("light_wisp",
		EntityType.Builder.of(LightWisp::new, MobCategory.AMBIENT).sized(0.4F, 0.4F).eyeHeight(0.2F).clientTrackingRange(8));
	public static final EntityType<Angel> ANGEL = register("angel",
		EntityType.Builder.of(Angel::new, MobCategory.CREATURE).sized(0.6F, 1.95F).eyeHeight(1.62F).clientTrackingRange(10));
	public static final EntityType<Pegasus> PEGASUS = register("pegasus",
		EntityType.Builder.of(Pegasus::new, MobCategory.CREATURE).sized(1.3964844F, 1.6F).eyeHeight(1.52F).passengerAttachments(1.44375F).clientTrackingRange(10));

	public static final EntityType<FallenSeraph> FALLEN_SERAPH = register("fallen_seraph",
		EntityType.Builder.of(FallenSeraph::new, MobCategory.MONSTER).fireImmune().sized(0.9F, 2.9F).eyeHeight(2.6F).clientTrackingRange(16));

	// Существа 0.2
	public static final EntityType<Cherub> CHERUB = register("cherub",
		EntityType.Builder.of(Cherub::new, MobCategory.CREATURE).sized(0.35F, 0.6F).clientTrackingRange(8).updateInterval(2));
	public static final EntityType<GoldenRam> GOLDEN_RAM = register("golden_ram",
		EntityType.Builder.of(GoldenRam::new, MobCategory.CREATURE).sized(0.9F, 1.3F).eyeHeight(1.235F).passengerAttachments(1.2375F).clientTrackingRange(10));
	public static final EntityType<SkyRay> SKY_RAY = register("sky_ray",
		EntityType.Builder.of(SkyRay::new, MobCategory.CREATURE).sized(3.2F, 1.0F).eyeHeight(0.6F)
			.passengerAttachments(new net.minecraft.world.phys.Vec3(0.0, 1.0, 0.5), new net.minecraft.world.phys.Vec3(0.0, 1.0, -0.5),
				new net.minecraft.world.phys.Vec3(0.8, 1.0, 0.0), new net.minecraft.world.phys.Vec3(-0.8, 1.0, 0.0)).clientTrackingRange(10));
	public static final EntityType<CloudJelly> CLOUD_JELLY = register("cloud_jelly",
		EntityType.Builder.of(CloudJelly::new, MobCategory.AMBIENT).sized(1.4F, 1.1F).eyeHeight(0.6F).clientTrackingRange(8));
	public static final EntityType<Mimic> MIMIC = register("mimic",
		EntityType.Builder.of(Mimic::new, MobCategory.MONSTER).sized(0.9F, 0.9F).eyeHeight(0.6F).clientTrackingRange(8));
	public static final EntityType<StormElemental> STORM_ELEMENTAL = register("storm_elemental",
		EntityType.Builder.of(StormElemental::new, MobCategory.MONSTER).fireImmune().sized(1.5F, 4.5F).eyeHeight(3.8F).clientTrackingRange(12));

	// Угасание
	public static final EntityType<dev.celestial.fading.Shadow> SHADOW = register("shadow",
		EntityType.Builder.of(dev.celestial.fading.Shadow::new, MobCategory.MONSTER).sized(0.6F, 1.95F).eyeHeight(1.74F).clientTrackingRange(8));
	public static final EntityType<dev.celestial.fading.Meteor> METEOR = registerNoEgg("meteor",
		EntityType.Builder.<dev.celestial.fading.Meteor>of(dev.celestial.fading.Meteor::new, MobCategory.MISC).noLootTable().sized(1.0F, 1.0F)
			.clientTrackingRange(16).updateInterval(2));

	// Снаряды (без яиц призыва)
	public static final EntityType<StarArrow> STAR_ARROW = registerNoEgg("star_arrow",
		EntityType.Builder.<StarArrow>of(StarArrow::new, MobCategory.MISC).noLootTable().sized(0.5F, 0.5F).eyeHeight(0.13F).clientTrackingRange(4).updateInterval(20));
	public static final EntityType<LightSpear> LIGHT_SPEAR = registerNoEgg("light_spear",
		EntityType.Builder.<LightSpear>of(LightSpear::new, MobCategory.MISC).noLootTable().sized(0.4F, 0.4F).clientTrackingRange(4).updateInterval(10));

	private ModEntities() {}

	private static <T extends Entity> EntityType<T> registerNoEgg(String name, EntityType.Builder<T> builder) {
		ResourceKey<EntityType<?>> key = ResourceKey.create(Registries.ENTITY_TYPE, Celestial.id(name));
		return Registry.register(BuiltInRegistries.ENTITY_TYPE, key, builder.build(key));
	}

	private static <T extends Entity> EntityType<T> register(String name, EntityType.Builder<T> builder) {
		ResourceKey<EntityType<?>> key = ResourceKey.create(Registries.ENTITY_TYPE, Celestial.id(name));
		EntityType<T> type = Registry.register(BuiltInRegistries.ENTITY_TYPE, key, builder.build(key));
		ModItems.register(name + "_spawn_egg", Item::new, new Item.Properties().spawnEgg(type));
		return type;
	}

	public static void init() {
		FabricDefaultAttributeRegistry.register(FALLEN_GUARDIAN, FallenGuardian.createAttributes());
		FabricDefaultAttributeRegistry.register(STORM_SPIRIT, StormSpirit.createAttributes());
		FabricDefaultAttributeRegistry.register(WINGED_SERPENT, WingedSerpent.createAttributes());
		FabricDefaultAttributeRegistry.register(CLOUD_WHALE, CloudWhale.createAttributes());
		FabricDefaultAttributeRegistry.register(LIGHT_WISP, LightWisp.createAttributes());
		FabricDefaultAttributeRegistry.register(ANGEL, Angel.createAttributes());
		FabricDefaultAttributeRegistry.register(PEGASUS, Pegasus.createAttributes());
		FabricDefaultAttributeRegistry.register(FALLEN_SERAPH, FallenSeraph.createAttributes());
		FabricDefaultAttributeRegistry.register(CHERUB, net.minecraft.world.entity.animal.allay.Allay.createAttributes());
		FabricDefaultAttributeRegistry.register(GOLDEN_RAM, net.minecraft.world.entity.animal.sheep.Sheep.createAttributes());
		FabricDefaultAttributeRegistry.register(SKY_RAY, SkyRay.createAttributes());
		FabricDefaultAttributeRegistry.register(CLOUD_JELLY, CloudJelly.createAttributes());
		FabricDefaultAttributeRegistry.register(MIMIC, Mimic.createAttributes());
		FabricDefaultAttributeRegistry.register(STORM_ELEMENTAL, StormElemental.createAttributes());
		FabricDefaultAttributeRegistry.register(SHADOW, dev.celestial.fading.Shadow.createAttributes());
		SpawnPlacements.register(CHERUB, SpawnPlacementTypes.NO_RESTRICTIONS, Heightmap.Types.MOTION_BLOCKING,
			(type, level, reason, pos, random) -> level.getBlockState(pos).isAir());
		SpawnPlacements.register(GOLDEN_RAM, SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
			(type, level, reason, pos, random) -> level.getBlockState(pos.below()).is(ModBlocks.GOLDEN_GRASS));
		SpawnPlacements.register(SKY_RAY, SpawnPlacementTypes.NO_RESTRICTIONS, Heightmap.Types.MOTION_BLOCKING,
			(type, level, reason, pos, random) -> level.getBlockState(pos).isAir() && level.getBlockState(pos.above(2)).isAir());
		SpawnPlacements.register(CLOUD_JELLY, SpawnPlacementTypes.NO_RESTRICTIONS, Heightmap.Types.MOTION_BLOCKING,
			(type, level, reason, pos, random) -> level.getBlockState(pos).isAir());
		SpawnPlacements.register(STORM_ELEMENTAL, SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
			(type, level, reason, pos, random) -> random.nextInt(8) == 0 && Monster.checkMonsterSpawnRules(type, level, reason, pos, random));

		SpawnPlacements.register(FALLEN_GUARDIAN, SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, Monster::checkMonsterSpawnRules);
		SpawnPlacements.register(STORM_SPIRIT, SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, Monster::checkMonsterSpawnRules);
		SpawnPlacements.register(WINGED_SERPENT, SpawnPlacementTypes.NO_RESTRICTIONS, Heightmap.Types.MOTION_BLOCKING,
			(type, level, reason, pos, random) -> level.getDifficulty() != Difficulty.PEACEFUL && level.getBlockState(pos).isAir() && random.nextInt(3) == 0);
		SpawnPlacements.register(CLOUD_WHALE, SpawnPlacementTypes.NO_RESTRICTIONS, Heightmap.Types.MOTION_BLOCKING,
			(type, level, reason, pos, random) -> level.getBlockState(pos).isAir() && level.getBlockState(pos.above(3)).isAir());
		SpawnPlacements.register(LIGHT_WISP, SpawnPlacementTypes.NO_RESTRICTIONS, Heightmap.Types.MOTION_BLOCKING,
			(type, level, reason, pos, random) -> level.getBlockState(pos).isAir());
		SpawnPlacements.register(ANGEL, SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
			(type, level, reason, pos, random) -> level.getBlockState(pos.below()).is(ModBlocks.GOLDEN_GRASS));
		SpawnPlacements.register(PEGASUS, SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
			(type, level, reason, pos, random) -> level.getBlockState(pos.below()).is(ModBlocks.GOLDEN_GRASS));
	}
}
