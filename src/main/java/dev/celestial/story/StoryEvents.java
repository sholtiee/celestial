package dev.celestial.story;

import dev.celestial.registry.ModItems;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.loot.v3.LootTableEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.boss.enderdragon.EnderDragon;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.storage.loot.BuiltInLootTables;
import net.minecraft.world.level.storage.loot.LootPool;
import net.minecraft.world.level.storage.loot.entries.LootItem;
import net.minecraft.world.level.storage.loot.predicates.LootItemRandomChanceCondition;

/** Связывает сюжет с миром: дневник при первом входе, Осколок Пламени в Аду, Сердце Пустоты от дракона. */
public final class StoryEvents {
	private StoryEvents() {}

	public static void init() {
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> server.execute(() -> giveJournalOnce(handler.player)));

		LootTableEvents.MODIFY.register((key, builder, source, registries) -> {
			if (!source.isBuiltin()) {
				return;
			}
			if (key.equals(BuiltInLootTables.NETHER_BRIDGE)) {
				builder.withPool(chancePool(ModItems.FLAME_SHARD, 0.35F));
			} else if (key.equals(BuiltInLootTables.BASTION_TREASURE) || key.equals(BuiltInLootTables.BASTION_OTHER)) {
				builder.withPool(chancePool(ModItems.FLAME_SHARD, 0.5F));
			} else if (key.equals(net.minecraft.world.entity.EntityTypes.FOX.getDefaultLootTable().orElse(null))) {
				builder.withPool(chancePool(ModItems.FUR, 0.6F));
			} else if (key.equals(BuiltInLootTables.END_CITY_TREASURE)) {
				builder.withPool(chancePool(ModItems.VOID_HEART, 0.15F));
			}
		});

		ServerLivingEntityEvents.AFTER_DEATH.register(StoryEvents::afterDeath);
	}

	private static LootPool.Builder chancePool(Item item, float chance) {
		return LootPool.lootPool().add(LootItem.lootTableItem(item)).when(LootItemRandomChanceCondition.randomChance(chance));
	}

	private static void giveJournalOnce(ServerPlayer player) {
		if (Story.ROOT.isDone(player) || player.getInventory().contains(new ItemStack(ModItems.WANDERER_JOURNAL))) {
			return;
		}
		ItemStack journal = new ItemStack(ModItems.WANDERER_JOURNAL);
		if (!player.getInventory().add(journal)) {
			player.spawnAtLocation(player.level(), journal);
		}
		player.sendSystemMessage(Component.translatable("story.celestial.dream"));
	}

	/** Дракон Энда всегда роняет Сердце Пустоты (каждое убийство), блейзы изредка — Осколок Пламени. */
	private static void afterDeath(LivingEntity entity, DamageSource source) {
		if (!(entity.level() instanceof ServerLevel level)) {
			return;
		}
		if (entity instanceof EnderDragon) {
			ItemEntity heart = new ItemEntity(level, entity.getX(), Math.max(entity.getY(), 70), entity.getZ(), new ItemStack(ModItems.VOID_HEART));
			heart.setGlowingTag(true);
			heart.setUnlimitedLifetime();
			level.addFreshEntity(heart);
			level.getPlayers(p -> p.distanceToSqr(entity) < 256 * 256)
				.forEach(p -> p.sendSystemMessage(Component.translatable("story.celestial.void_heart_drop")));
		} else if (entity.getType() == net.minecraft.world.entity.EntityTypes.BLAZE && source.getEntity() instanceof Player
			&& level.getRandom().nextFloat() < 0.04F) {
			entity.spawnAtLocation(level, new ItemStack(ModItems.FLAME_SHARD));
		}
	}

	public static void onHeavenPortalLit(Player player) {
		if (player instanceof ServerPlayer serverPlayer) {
			serverPlayer.sendSystemMessage(Component.translatable("story.celestial.portal_lit"));
		}
	}

	public static void onSeraphDefeated(ServerLevel level, LivingEntity seraph, DamageSource source) {
		level.getPlayers(p -> p.distanceToSqr(seraph) < 96 * 96).forEach(p -> {
			Story.SERAPH.grant(p);
			p.sendSystemMessage(Component.translatable("story.celestial.seraph_defeated"));
			// Осколок Света нельзя потерять: Печать будит Серафима один раз, а без осколка закрыты и финал, и всё дальше.
			// Выдаём каждому участнику прямо в инвентарь; если места нет — предмет лежит вечно.
			ItemStack shard = new ItemStack(ModItems.LIGHT_SHARD);
			if (!p.getInventory().add(shard)) {
				ItemEntity drop = p.spawnAtLocation(level, shard);
				if (drop != null) {
					drop.setUnlimitedLifetime();
					drop.setGlowingTag(true);
				}
			}
		});
	}

	/** Акт II пройден: Пожиратель Света повержен — Тёмное Ядро, титры, Угасание отступает ещё на ступень. */
	public static void onDevourerDefeated(ServerLevel level, LivingEntity boss) {
		ItemEntity core = new ItemEntity(level, boss.getX(), boss.getY(), boss.getZ(), new ItemStack(ModItems.DARK_CORE));
		core.setGlowingTag(true);
		core.setUnlimitedLifetime();
		level.addFreshEntity(core);
		for (ServerPlayer p : level.getPlayers(p -> p.distanceToSqr(boss) < 96 * 96)) {
			Story.DEVOURER.grant(p);
			dev.celestial.data.CelestialData.update(p, d -> d.withGrace(d.grace() + 6));
			p.connection.send(new net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket(20, 100, 40));
			p.connection.send(new net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket(Component.translatable("story.celestial.act2.title")));
			p.connection.send(new net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket(Component.translatable("story.celestial.act2.subtitle")));
			for (int i = 1; i <= 3; i++) {
				p.sendSystemMessage(Component.translatable("story.celestial.act2." + i));
			}
		}
		var server = level.getServer();
		if (dev.celestial.data.CelestialData.world(server).act() < 2) {
			dev.celestial.data.CelestialData.updateWorld(server, w -> w.withAct(2).withFlag("act2_done"));
			dev.celestial.fading.Fading.weaken(server, 1);
		}
	}

	/** Финал: все три осколка на алтаре. */
	public static void onAltarComplete(ServerLevel level, net.minecraft.core.BlockPos altar) {
		level.playSound(null, altar, SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.BLOCKS, 3.0F, 1.0F);
		level.playSound(null, altar, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 3.0F, 1.0F);
		for (int i = 0; i < 40; i++) {
			level.sendParticles(ParticleTypes.END_ROD, altar.getX() + 0.5, altar.getY() + 1 + i * 0.6, altar.getZ() + 0.5, 6, 0.15, 0.2, 0.15, 0.02);
		}
		level.sendParticles(ParticleTypes.FIREWORK, altar.getX() + 0.5, altar.getY() + 3, altar.getZ() + 0.5, 200, 2.0, 2.0, 2.0, 0.3);
		for (ServerPlayer p : level.getPlayers(p -> p.distanceToSqr(net.minecraft.world.phys.Vec3.atCenterOf(altar)) < 96 * 96)) {
			Story.FINALE.grant(p);
			Finale.play(p);
			dev.celestial.data.CelestialData.update(p, d -> d.withGrace(d.grace() + 5));
		}
		// Акт I пройден: свет вернулся лишь частично — Угасание отступает на две ступени
		var server = level.getServer();
		if (dev.celestial.data.CelestialData.world(server).act() < 1) {
			dev.celestial.data.CelestialData.updateWorld(server, w -> w.withAct(1).withFlag("act1_done"));
			dev.celestial.fading.Fading.weaken(server, 2);
		}
	}
}
