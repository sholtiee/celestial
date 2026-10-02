package dev.celestial.registry;

import dev.celestial.Celestial;
import dev.celestial.entity.Angel;
import dev.celestial.entity.CloudWhale;
import dev.celestial.entity.FallenGuardian;
import dev.celestial.entity.LightWisp;
import dev.celestial.entity.Pegasus;
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

	private ModEntities() {}

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
