package dev.celestial.entity;

import dev.celestial.Celestial;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.animal.sheep.Sheep;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.storage.loot.LootTable;
import org.jspecify.annotations.Nullable;

/** Златорунный баран: при стрижке даёт золотое руно (своя таблица добычи). */
public class GoldenRam extends Sheep {
	public static final ResourceKey<LootTable> SHEARING = ResourceKey.create(Registries.LOOT_TABLE, Celestial.id("shearing/golden_ram"));

	public GoldenRam(EntityType<? extends GoldenRam> type, Level level) {
		super(type, level);
	}

	@Override
	public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason, @Nullable SpawnGroupData data) {
		SpawnGroupData result = super.finalizeSpawn(level, difficulty, reason, data);
		setColor(DyeColor.YELLOW);
		return result;
	}

	@Override
	public void shear(ServerLevel level, SoundSource source, ItemStack tool) {
		level.playSound(null, this, SoundEvents.SHEEP_SHEAR, source, 1.0F, 1.2F);
		dropFromShearingLootTable(level, SHEARING, tool, (l, drop) -> spawnAtLocation(l, drop, 1.0F));
		setSheared(true);
	}
}
