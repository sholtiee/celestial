package dev.celestial.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import dev.celestial.data.CelestialData;
import dev.celestial.data.PlayerData;
import dev.celestial.data.WorldState;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;

/** /celestial — состояние саги и отладка: status, fading <0-5>, act <n>, grace <n>, skill <id>, codex <id>. */
public final class CelestialCommand {
	private CelestialCommand() {}

	public static void init() {
		CommandRegistrationCallback.EVENT.register((dispatcher, context, selection) -> register(dispatcher));
	}

	private static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
		dispatcher.register(Commands.literal("celestial")
			.then(Commands.literal("status").executes(ctx -> {
				CommandSourceStack src = ctx.getSource();
				WorldState world = CelestialData.world(src.getServer());
				src.sendSuccess(() -> Component.literal("§6Угасание: §f" + world.fading() + "/5 §6Акт: §f" + world.act()
					+ " §6Флаги: §f" + world.flags()), false);
				if (src.getEntity() instanceof ServerPlayer player) {
					PlayerData data = CelestialData.get(player);
					src.sendSuccess(() -> Component.literal("§bБлагодать: §f" + data.grace() + " §bНавыки: §f" + data.skills()
						+ " §bРепутация: §f" + data.reputation() + " §bСияние: §f" + (int) data.radiance() + " §bСтрах: §f" + (int) data.fear() + " §bТепло: §f" + (int) data.warmth()
						+ " §bИспытания: §f" + data.trials() + " §bКодекс: §f" + data.codex().size()), false);
					// диагностика тьмы: что сейчас считает Darkness
					var eyes = net.minecraft.core.BlockPos.containing(player.getEyePosition());
					src.sendSuccess(() -> Component.literal("§8Тьма: мир=" + player.level().dimension().identifier()
						+ " бездна=" + dev.celestial.world.abyss.Darkness.inAbyss(player)
						+ " свет_у_глаз=" + player.level().getBrightness(net.minecraft.world.level.LightLayer.BLOCK, eyes)
						+ " свет_в_руке=" + dev.celestial.world.abyss.Darkness.holdsLight(player)
						+ " оберег=" + dev.celestial.starlight.Wards.protects(player.level(), player.blockPosition())
						+ " сияние=" + player.hasEffect(dev.celestial.registry.ModEffects.STARLIGHT)
						+ " режим=" + player.gameMode.getGameModeForPlayer()
						+ " у_огня=" + dev.celestial.world.frozen.Cold.nearHeat(player.level(), player.blockPosition())
						+ " поз=" + player.blockPosition().toShortString()), false);
				}
				return 1;
			}))
			.then(Commands.literal("fading").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
				.then(Commands.argument("stage", IntegerArgumentType.integer(0, WorldState.MAX_FADING)).executes(ctx -> {
					int stage = IntegerArgumentType.getInteger(ctx, "stage");
					CelestialData.updateWorld(ctx.getSource().getServer(), w -> w.withFading(stage));
					ctx.getSource().sendSuccess(() -> Component.literal("Угасание: " + stage), true);
					return stage;
				})))
			.then(Commands.literal("act").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
				.then(Commands.argument("act", IntegerArgumentType.integer(0, 5)).executes(ctx -> {
					int act = IntegerArgumentType.getInteger(ctx, "act");
					CelestialData.updateWorld(ctx.getSource().getServer(), w -> new dev.celestial.data.WorldState(w.fading(), act, w.flags(), w.lastFadingDay()));
					ctx.getSource().sendSuccess(() -> Component.literal("Акт: " + act), true);
					return act;
				})))
			.then(Commands.literal("grace").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
				.then(Commands.argument("amount", IntegerArgumentType.integer()).executes(ctx -> {
					int amount = IntegerArgumentType.getInteger(ctx, "amount");
					ServerPlayer player = ctx.getSource().getPlayerOrException();
					PlayerData data = CelestialData.update(player, d -> d.withGrace(d.grace() + amount));
					ctx.getSource().sendSuccess(() -> Component.literal("Благодать: " + data.grace()), true);
					return data.grace();
				})))
			.then(Commands.literal("meteor").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS)).executes(ctx -> {
				ServerPlayer player = ctx.getSource().getPlayerOrException();
				return dev.celestial.fading.Meteors.fallNear(player.level(), player) ? 1 : 0;
			}).then(Commands.argument("pos", net.minecraft.commands.arguments.coordinates.BlockPosArgument.blockPos()).executes(ctx -> {
				var raw = net.minecraft.commands.arguments.coordinates.BlockPosArgument.getBlockPos(ctx, "pos");
				var pos = ctx.getSource().getLevel().getHeightmapPos(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, raw);
				var target = net.minecraft.world.phys.Vec3.atCenterOf(pos);
				dev.celestial.fading.Meteor.launch(ctx.getSource().getLevel(), target.add(30, 90, 10), target);
				return 1;
			})))
			.then(Commands.literal("forget").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS)).executes(ctx -> {
				CelestialData.update(ctx.getSource().getPlayerOrException(), PlayerData::withoutSkills);
				ctx.getSource().sendSuccess(() -> Component.literal("Навыки забыты (для тестов)"), true);
				return 1;
			}))
			.then(Commands.literal("learn")
				.then(Commands.argument("skill", StringArgumentType.word()).executes(ctx ->
					dev.celestial.grace.Grace.learn(ctx.getSource().getPlayerOrException(), StringArgumentType.getString(ctx, "skill")) ? 1 : 0)))
			.then(Commands.literal("beacon")
				.then(Commands.argument("pos", net.minecraft.commands.arguments.coordinates.BlockPosArgument.blockPos())
					.then(Commands.argument("dimension", net.minecraft.commands.arguments.IdentifierArgument.id()).executes(ctx -> {
						ServerPlayer player = ctx.getSource().getPlayerOrException();
						net.minecraft.core.BlockPos target = net.minecraft.commands.arguments.coordinates.BlockPosArgument.getBlockPos(ctx, "pos");
						var dimId = net.minecraft.commands.arguments.IdentifierArgument.getId(ctx, "dimension");
						return dev.celestial.block.machine.BeaconTravel.travel(player, target, dimId);
					}))))
			.then(Commands.literal("quest")
				.then(Commands.literal("take").then(Commands.argument("board", net.minecraft.commands.arguments.coordinates.BlockPosArgument.blockPos())
					.then(Commands.argument("index", IntegerArgumentType.integer(0, 9)).executes(ctx -> dev.celestial.quest.Quests.take(
						ctx.getSource().getPlayerOrException(),
						net.minecraft.commands.arguments.coordinates.BlockPosArgument.getBlockPos(ctx, "board"), IntegerArgumentType.getInteger(ctx, "index"))))))
				.then(Commands.literal("turnin").then(Commands.argument("board", net.minecraft.commands.arguments.coordinates.BlockPosArgument.blockPos())
					.executes(ctx -> dev.celestial.quest.Quests.turnIn(ctx.getSource().getPlayerOrException(),
						net.minecraft.commands.arguments.coordinates.BlockPosArgument.getBlockPos(ctx, "board"))))))
			.then(Commands.literal("lore").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
				.then(Commands.literal("unlock").then(Commands.argument("sheet", StringArgumentType.word()).executes(ctx -> loreChange(ctx, true))))
				.then(Commands.literal("lock").then(Commands.argument("sheet", StringArgumentType.word()).executes(ctx -> loreChange(ctx, false))))
				.then(Commands.literal("gloss").then(Commands.argument("word", StringArgumentType.word()).executes(ctx -> {
					boolean added = dev.celestial.lore.Lore.addGlossary(ctx.getSource().getPlayerOrException(), StringArgumentType.getString(ctx, "word"), true);
					ctx.getSource().sendSuccess(() -> Component.translatable("lore.celestial.cmd.gloss", added ? 1 : 0), true);
					return added ? 1 : 0;
				}))))
			.then(Commands.literal("codex").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
				.then(Commands.argument("entry", StringArgumentType.greedyString()).executes(ctx -> {
					String entry = StringArgumentType.getString(ctx, "entry");
					CelestialData.update(ctx.getSource().getPlayerOrException(), d -> d.withCodex(entry));
					ctx.getSource().sendSuccess(() -> Component.literal("Кодекс: + " + entry), true);
					return 1;
				}))));
	}

	/** /celestial lore unlock|lock <лист|all> — открыть или закрыть лист Летописи (для тестов). */
	private static int loreChange(com.mojang.brigadier.context.CommandContext<net.minecraft.commands.CommandSourceStack> ctx, boolean open)
		throws com.mojang.brigadier.exceptions.CommandSyntaxException {
		ServerPlayer player = ctx.getSource().getPlayerOrException();
		String id = StringArgumentType.getString(ctx, "sheet");
		java.util.List<String> ids = id.equals("all") ? dev.celestial.lore.Lore.sheets().stream().map(dev.celestial.lore.Lore.Sheet::id).toList() : java.util.List.of(id);
		if (!id.equals("all") && dev.celestial.lore.Lore.sheet(id).isEmpty()) {
			ctx.getSource().sendFailure(Component.translatable("lore.celestial.unknown", id));
			return 0;
		}
		int changed = 0;
		for (String sheet : ids) {
			changed += (open ? dev.celestial.lore.Lore.unlock(player, sheet) : dev.celestial.lore.Lore.lock(player, sheet)) ? 1 : 0;
		}
		final int count = changed;
		ctx.getSource().sendSuccess(() -> Component.translatable(open ? "lore.celestial.cmd.unlocked" : "lore.celestial.cmd.locked", count), true);
		return count;
	}
}
