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

	public static final BlockEntityType<dev.celestial.world.abyss.AbyssRiftBlockEntity> ABYSS_RIFT = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("abyss_rift"),
		new BlockEntityType<>(dev.celestial.world.abyss.AbyssRiftBlockEntity::new, Set.of(ModBlocks.ABYSS_RIFT)));
	public static final BlockEntityType<dev.celestial.starlight.StarCollectorBlockEntity> STAR_COLLECTOR = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("star_collector"),
		new BlockEntityType<>(dev.celestial.starlight.StarCollectorBlockEntity::new, Set.of(ModBlocks.STAR_COLLECTOR)));
	public static final BlockEntityType<dev.celestial.starlight.WardBlockEntity> WARD = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("ward"),
		new BlockEntityType<>(dev.celestial.starlight.WardBlockEntity::new, Set.of(ModBlocks.WARD)));
	public static final BlockEntityType<dev.celestial.boss.DevourerSealBlockEntity> DEVOURER_SEAL = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("devourer_seal"),
		new BlockEntityType<>(dev.celestial.boss.DevourerSealBlockEntity::new, Set.of(ModBlocks.DEVOURER_SEAL)));
	public static final BlockEntityType<dev.celestial.block.light.BeamSourceBlockEntity> BEAM_SOURCE = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("beam_source"),
		new BlockEntityType<>(dev.celestial.block.light.BeamSourceBlockEntity::new, Set.of(ModBlocks.SUN_LENS, ModBlocks.BEAM_LANTERN)));
	public static final BlockEntityType<dev.celestial.block.puzzle.ReliquaryBlockEntity> RELIQUARY = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("reliquary"),
		new BlockEntityType<>(dev.celestial.block.puzzle.ReliquaryBlockEntity::new, Set.of(ModBlocks.RELIQUARY)));
	public static final BlockEntityType<dev.celestial.block.lore.LoreTabletBlockEntity> LORE_TABLET = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("lore_tablet"),
		new BlockEntityType<>(dev.celestial.block.lore.LoreTabletBlockEntity::new, Set.of(ModBlocks.LORE_TABLET)));
	public static final BlockEntityType<dev.celestial.block.puzzle.BellAltarBlockEntity> BELL_ALTAR = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("bell_altar"),
		new BlockEntityType<>(dev.celestial.block.puzzle.BellAltarBlockEntity::new, Set.of(ModBlocks.BELL_ALTAR)));

	public static final BlockEntityType<dev.celestial.block.machine.CloudLiftBlockEntity> CLOUD_LIFT = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("cloud_lift"),
		new BlockEntityType<>(dev.celestial.block.machine.CloudLiftBlockEntity::new, Set.of(ModBlocks.CLOUD_LIFT)));

	public static final BlockEntityType<dev.celestial.trial.TrialControllerBlockEntity> TRIAL_CONTROLLER = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("trial_crystal"),
		new BlockEntityType<>(dev.celestial.trial.TrialControllerBlockEntity::new, Set.of(ModBlocks.TRIAL_CONTROLLER)));

	public static final BlockEntityType<dev.celestial.block.puzzle.ice.GlacierHallBlockEntity> GLACIER_HALL = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("glacier_hall"),
		new BlockEntityType<>(dev.celestial.block.puzzle.ice.GlacierHallBlockEntity::new, Set.of(ModBlocks.ICE_BELL)));

	public static final BlockEntityType<dev.celestial.block.puzzle.BeamLockBlockEntity> BEAM_LOCK = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("beam_lock"),
		new BlockEntityType<>(dev.celestial.block.puzzle.BeamLockBlockEntity::new, Set.of(ModBlocks.BEAM_LOCK)));

	public static final BlockEntityType<dev.celestial.block.puzzle.ice.HallSealBlock.Entity> HALL_SEAL = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("hall_seal"),
		new BlockEntityType<>(dev.celestial.block.puzzle.ice.HallSealBlock.Entity::new, Set.of(ModBlocks.HALL_SEAL)));

	public static final BlockEntityType<dev.celestial.boss.ArchonSealBlockEntity> ARCHON_SEAL = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("archon_seal"),
		new BlockEntityType<>(dev.celestial.boss.ArchonSealBlockEntity::new, Set.of(ModBlocks.ARCHON_SEAL)));

	public static final BlockEntityType<dev.celestial.block.puzzle.star.StarLockBlockEntity> STAR_LOCK = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("star_lock"),
		new BlockEntityType<>(dev.celestial.block.puzzle.star.StarLockBlockEntity::new, Set.of(ModBlocks.STAR_LOCK)));

	public static final BlockEntityType<dev.celestial.block.puzzle.memory.MemoryAltarBlockEntity> MEMORY_ALTAR = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("memory_altar"),
		new BlockEntityType<>(dev.celestial.block.puzzle.memory.MemoryAltarBlockEntity::new, Set.of(ModBlocks.MEMORY_ALTAR)));

	public static final BlockEntityType<dev.celestial.block.puzzle.echo.EchoAltarBlockEntity> ECHO_ALTAR = Registry.register(
		BuiltInRegistries.BLOCK_ENTITY_TYPE, Celestial.id("echo_altar"),
		new BlockEntityType<>(dev.celestial.block.puzzle.echo.EchoAltarBlockEntity::new, Set.of(ModBlocks.ECHO_ALTAR)));

	private ModBlockEntities() {}

	public static void init() {
	}
}
