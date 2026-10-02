package dev.celestial.fading;

import com.google.common.collect.ImmutableSet;
import dev.celestial.Celestial;
import dev.celestial.registry.ModBlocks;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import net.fabricmc.fabric.api.object.builder.v1.world.poi.PoiHelper;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.ai.village.poi.PoiType;
import net.minecraft.world.entity.npc.villager.VillagerProfession;
import net.minecraft.world.item.trading.TradeSet;

/** Звездочёт: профессия жителя с Телескопом. Торгует звёздными товарами и картами к Звёздной обсерватории. */
public final class Stargazer {
	public static final ResourceKey<PoiType> POI = ResourceKey.create(Registries.POINT_OF_INTEREST_TYPE, Celestial.id("stargazer"));
	public static final ResourceKey<VillagerProfession> PROFESSION = ResourceKey.create(Registries.VILLAGER_PROFESSION, Celestial.id("stargazer"));

	private Stargazer() {}

	public static void init() {
		PoiHelper.register(POI.identifier(), 1, 1, ModBlocks.TELESCOPE);
		Int2ObjectMap<ResourceKey<TradeSet>> trades = new it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap<>();
		for (int level = 1; level <= 5; level++) {
			trades.put(level, ResourceKey.create(Registries.TRADE_SET, Celestial.id("stargazer/level_" + level)));
		}
		Registry.register(BuiltInRegistries.VILLAGER_PROFESSION, PROFESSION, new VillagerProfession(
			Component.translatable("entity.celestial.villager.stargazer"),
			poi -> poi.is(POI), poi -> poi.is(POI), ImmutableSet.of(), ImmutableSet.of(),
			SoundEvents.VILLAGER_WORK_CARTOGRAPHER, trades));
	}
}
