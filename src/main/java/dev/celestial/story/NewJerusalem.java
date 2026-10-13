package dev.celestial.story;

import dev.celestial.Celestial;
import dev.celestial.data.CelestialData;
import dev.celestial.world.dim.AbyssFeatures;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.portal.TeleportTransition;
import net.minecraft.world.phys.Vec3;

/**
 * Новый Иерусалим (Откр. 21–22) — эпилог светлых концовок («Возжечь» и «Имя»). Город сходит в Астрал один раз на мир:
 * шаблон {@code celestial:new_jerusalem/city} (tools/gen_jerusalem.py) ставится по требованию в {@link #CENTER} (уровень золотой улицы).
 * Через 10 с после концовки бойцы переносятся к южным вратам; потом в город ведёт ПКМ по Звёздному алтарю, домой — свет престола.
 */
public final class NewJerusalem {
	/** Центр города на уровне улицы (блок мостовой). Далеко от алтаря (у центра мира) и от отражений Безликого (+Z). */
	public static final BlockPos CENTER = new BlockPos(0, 150, -720);
	/** Как в gen_jerusalem.py: полуширина шаблона (с площадками за воротами), полуширина стены, слоёв основания под улицей. */
	public static final int HALF = 37, WALL = 33, BELOW = 12;
	/** Запас чистого неба вокруг шаблона. */
	private static final int CLEAR = 18;
	public static final String FLAG = "new_jerusalem";
	private static final Map<UUID, Integer> PENDING = new HashMap<>();

	private NewJerusalem() {}

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(NewJerusalem::tick);
	}

	/** Город открыт после светлой концовки. */
	public static boolean open(MinecraftServer server) {
		var w = CelestialData.world(server);
		return w.has("ending_" + Endings.KINDLE) || w.has("ending_" + Endings.NAME);
	}

	public static void schedule(ServerPlayer p, int delay) {
		PENDING.put(p.getUUID(), p.level().getServer().getTickCount() + delay);
	}

	private static void tick(MinecraftServer server) {
		if (PENDING.isEmpty()) {
			return;
		}
		int now = server.getTickCount();
		PENDING.entrySet().removeIf(e -> {
			if (e.getValue() > now) {
				return false;
			}
			ServerPlayer p = server.getPlayerList().getPlayer(e.getKey());
			if (p != null) {
				bring(p);
			}
			return true;
		});
	}

	/** Поставить город (раз на мир). */
	public static boolean build(ServerLevel astral) {
		MinecraftServer server = astral.getServer();
		if (CelestialData.world(server).has(FLAG)) {
			return true;
		}
		var template = server.getStructureTemplateManager().get(Celestial.id("new_jerusalem/city"));
		if (template.isEmpty()) {
			return false;
		}
		clearSky(astral);
		BlockPos origin = CENTER.offset(-HALF, -BELOW, -HALF);
		template.get().placeInWorld(astral, origin, origin, new StructurePlaceSettings(), astral.getRandom(), 2);
		CelestialData.updateWorld(server, w -> w.withFlag(FLAG));
		return true;
	}

	/** Расчистить небо вокруг города: астероиды не должны упираться в стены и висеть перед воротами. */
	private static void clearSky(ServerLevel level) {
		int r = HALF + CLEAR;
		BlockPos.MutableBlockPos m = new BlockPos.MutableBlockPos();
		for (int x = -r; x <= r; x++) {
			for (int z = -r; z <= r; z++) {
				for (int y = -BELOW - CLEAR; y <= 34 + CLEAR; y++) {
					m.set(CENTER.getX() + x, CENTER.getY() + y, CENTER.getZ() + z);
					if (!level.getBlockState(m).isAir()) {
						level.setBlock(m, net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(), 2 | 16);
					}
				}
			}
		}
	}

	/** Перенести игрока к южным вратам, лицом к престолу. */
	public static void bring(ServerPlayer p) {
		MinecraftServer server = p.level().getServer();
		ServerLevel astral = server.getLevel(AbyssFeatures.ASTRAL);
		if (astral == null || !build(astral)) {
			return;
		}
		Vec3 to = Vec3.atBottomCenterOf(CENTER.offset(0, 1, WALL - 4));
		p.teleport(new TeleportTransition(astral, to, Vec3.ZERO, 180.0F, -5.0F, TeleportTransition.DO_NOTHING));
		p.resetFallDistance();
		astral.sendParticles(ParticleTypes.END_ROD, to.x, to.y + 1, to.z, 40, 0.5, 1.0, 0.5, 0.05);
		astral.playSound(null, BlockPos.containing(to), SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 1.0F, 1.2F);
		boolean first = !CelestialData.get(p).knows("place:" + FLAG);
		CelestialData.update(p, d -> d.withCodex("place:" + FLAG));
		if (first) {
			dev.celestial.boss.BossIntro.title(p, Component.translatable("jerusalem.celestial.title").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD),
				Component.translatable("jerusalem.celestial.subtitle").withStyle(ChatFormatting.ITALIC), 120);
			for (int i = 1; i <= 3; i++) {
				p.sendSystemMessage(Component.translatable("jerusalem.celestial.welcome." + i).withStyle(ChatFormatting.YELLOW));
			}
		}
	}

	/** Свет престола: домой, к точке появления Верхнего мира. */
	public static void leave(ServerPlayer p) {
		MinecraftServer server = p.level().getServer();
		ServerLevel overworld = server.overworld();
		BlockPos spawn = server.getRespawnData().pos();
		overworld.getChunkAt(spawn);
		int y = overworld.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, spawn.getX(), spawn.getZ());
		Vec3 to = new Vec3(spawn.getX() + 0.5, y, spawn.getZ() + 0.5);
		p.teleport(new TeleportTransition(overworld, to, Vec3.ZERO, p.getYRot(), p.getXRot(), TeleportTransition.DO_NOTHING));
		p.resetFallDistance();
		p.sendSystemMessage(Component.translatable("jerusalem.celestial.leave").withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
	}
}
