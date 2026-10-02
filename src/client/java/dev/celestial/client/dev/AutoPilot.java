package dev.celestial.client.dev;

import dev.celestial.Celestial;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.Deque;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Dev-автопилот для проверки мода без ручного управления.
 * Включается только переменной окружения CELESTIAL_AUTOPILOT=путь/к/сценарию.
 * Строки сценария: "/команда", "wait N" (тики), "shot имя", "use X Y Z грань", "quit", "# комментарий".
 */
public final class AutoPilot {
	private static final Deque<String> steps = new ArrayDeque<>();
	private static int waitTicks;
	private static final java.util.Map<net.minecraft.client.KeyMapping, Integer> held = new java.util.HashMap<>();

	private AutoPilot() {}

	public static void init() {
		String script = System.getenv("CELESTIAL_AUTOPILOT");
		if (script == null || script.isBlank()) {
			return;
		}
		try {
			for (String line : Files.readAllLines(Path.of(script))) {
				line = line.strip();
				if (!line.isEmpty() && !line.startsWith("#")) {
					steps.add(line);
				}
			}
		} catch (IOException e) {
			Celestial.LOGGER.error("Автопилот: не удалось прочитать сценарий {}", script, e);
			return;
		}
		Celestial.LOGGER.info("Автопилот: {} шагов из {}", steps.size(), script);
		waitTicks = 100; // даём миру прогрузиться
		ClientTickEvents.END_CLIENT_TICK.register(AutoPilot::tick);
	}

	private static void gotoStructure(Minecraft mc, String id, double dx, double dy, double dz, float yaw, float pitch) {
		var server = mc.getSingleplayerServer();
		if (server == null) {
			return;
		}
		server.execute(() -> {
			var level = server.getLevel(dev.celestial.world.HeavenDimension.HEAVEN);
			var registry = level.registryAccess().lookupOrThrow(net.minecraft.core.registries.Registries.STRUCTURE);
			var holder = registry.getOrThrow(net.minecraft.resources.ResourceKey.create(net.minecraft.core.registries.Registries.STRUCTURE,
				net.minecraft.resources.Identifier.parse(id)));
			var player = server.getPlayerList().getPlayers().getFirst();
			var found = level.getChunkSource().getGenerator().findNearestMapStructure(level,
				net.minecraft.core.HolderSet.direct(holder), player.blockPosition(), 100, false);
			if (found == null) {
				Celestial.LOGGER.warn("Автопилот: структура {} не найдена", id);
				return;
			}
			BlockPos at = found.getFirst();
			var start = level.getChunk(at).getStartForStructure(holder.value());
			var box = start != null && start.isValid() ? start.getBoundingBox() : new net.minecraft.world.level.levelgen.structure.BoundingBox(at);
			var center = box.getCenter();
			Celestial.LOGGER.info("Автопилот: {} в {} (коробка {})", id, center, box);
			String cmd = String.format(java.util.Locale.ROOT, "execute in celestial:heaven run tp @s %.1f %.1f %.1f %.1f %.1f",
				center.getX() + dx + 0.5, box.maxY() + dy, center.getZ() + dz + 0.5, yaw, pitch);
			server.getCommands().performPrefixedCommand(player.createCommandSourceStack().withPermission(net.minecraft.server.permissions.LevelBasedPermissionSet.OWNER), cmd);
		});
	}

	private static void tick(Minecraft mc) {
		if (mc.player == null || mc.getConnection() == null || steps.isEmpty()) {
			return;
		}
		// удерживаемые клавиши (hold): держим нажатыми нужное число тиков
		held.replaceAll((key, ticks) -> {
			key.setDown(ticks > 1);
			return ticks - 1;
		});
		held.values().removeIf(t -> t <= 0);
		if (mc.player.isDeadOrDying()) {
			// игрок умер в прошлом прогоне — возрождаем, иначе клиент «застрянет» на экране смерти
			mc.player.respawn();
			mc.gui.setScreen(null);
			waitTicks = 40;
			return;
		}
		if (waitTicks > 0) {
			waitTicks--;
			return;
		}
		String step = steps.poll();
		Celestial.LOGGER.info("Автопилот: {}", step);
		if (step.startsWith("/")) {
			mc.getConnection().sendCommand(step.substring(1));
			waitTicks = 2;
		} else if (step.startsWith("wait ")) {
			waitTicks = Integer.parseInt(step.substring(5).strip());
		} else if (step.startsWith("shot ")) {
			String name = step.substring(5).strip() + ".png";
			Screenshot.grab(mc.gameDirectory, name, mc.gameRenderer.mainRenderTarget(), 1,
				msg -> Celestial.LOGGER.info("Автопилот: скриншот {}", msg.getString()));
			waitTicks = 5;
		} else if (step.startsWith("use ")) {
			// use X Y Z face — правый клик предметом в руке по блоку
			String[] a = step.substring(4).strip().split("\\s+");
			BlockPos pos = new BlockPos(Integer.parseInt(a[0]), Integer.parseInt(a[1]), Integer.parseInt(a[2]));
			Direction face = Direction.byName(a[3]);
			BlockHitResult hit = new BlockHitResult(Vec3.atCenterOf(pos).relative(face, 0.5), face, pos, false);
			mc.gameMode.useItemOn(mc.player, InteractionHand.MAIN_HAND, hit);
			waitTicks = 5;
		} else if (step.equals("clearchat")) {
			mc.gui.hud.getChat().clearMessages(false);
		} else if (step.equals("togglehud")) {
			mc.gui.hud.toggle();
		} else if (step.startsWith("camera ")) {
			// camera first|back|front
			mc.options.setCameraType(switch (step.substring(7).strip()) {
				case "back" -> net.minecraft.client.CameraType.THIRD_PERSON_BACK;
				case "front" -> net.minecraft.client.CameraType.THIRD_PERSON_FRONT;
				default -> net.minecraft.client.CameraType.FIRST_PERSON;
			});
		} else if (step.equals("fly")) {
			var server = mc.getSingleplayerServer();
			if (server != null) {
				server.execute(() -> server.getPlayerList().getPlayers().forEach(p -> {
					p.getAbilities().flying = true;
					p.onUpdateAbilities();
				}));
			}
		} else if (step.startsWith("goto ")) {
			// goto <id структуры> dx dy dz yaw pitch — относительно центра/верха найденной структуры
			String[] a = step.substring(5).strip().split("\\s+");
			gotoStructure(mc, a[0], Double.parseDouble(a[1]), Double.parseDouble(a[2]), Double.parseDouble(a[3]),
				Float.parseFloat(a[4]), Float.parseFloat(a[5]));
			waitTicks = 5;
		} else if (step.equals("pos")) {
			Celestial.LOGGER.info("Автопилот: позиция {} {} {} {} блок-под-ногами={}", mc.player.level().dimension().identifier(),
				(int) Math.floor(mc.player.getX()), String.format(java.util.Locale.ROOT, "%.2f", mc.player.getY()), (int) Math.floor(mc.player.getZ()),
				mc.player.level().getBlockState(mc.player.blockPosition()).getBlock());
		} else if (step.equals("useitem")) {
			mc.gameMode.useItem(mc.player, InteractionHand.MAIN_HAND);
			waitTicks = 5;
		} else if (step.startsWith("userel ")) {
			// userel dx dy dz грань — правый клик по блоку относительно позиции игрока
			String[] a = step.substring(7).strip().split("\\s+");
			BlockPos pos = mc.player.blockPosition().offset(Integer.parseInt(a[0]), Integer.parseInt(a[1]), Integer.parseInt(a[2]));
			Direction face = Direction.byName(a[3]);
			mc.gameMode.useItemOn(mc.player, InteractionHand.MAIN_HAND, new BlockHitResult(Vec3.atCenterOf(pos).relative(face, 0.5), face, pos, false));
			waitTicks = 5;
		} else if (step.equals("closescreen")) {
			mc.gui.setScreen(null);
		} else if (step.startsWith("hold ")) {
			// hold jump|forward|sneak|back|left|right|attack|use N — держать клавишу N тиков (не ждёт)
			String[] a = step.substring(5).strip().split("\\s+");
			var o = mc.options;
			net.minecraft.client.KeyMapping key = switch (a[0]) {
				case "jump" -> o.keyJump;
				case "forward" -> o.keyUp;
				case "back" -> o.keyDown;
				case "left" -> o.keyLeft;
				case "right" -> o.keyRight;
				case "sneak" -> o.keyShift;
				case "attack" -> o.keyAttack;
				default -> o.keyUse;
			};
			key.setDown(true);
			held.put(key, Integer.parseInt(a[1]));
		} else if (step.startsWith("codex ")) {
			// codex saga|grace|bestiary|places|guide — открыть вкладку Кодекса
			mc.gui.setScreen(dev.celestial.client.grace.CodexScreen.onTab(step.substring(6).strip()));
			waitTicks = 5;
		} else if (step.startsWith("press ")) {
			// press cast|cycle|dash|codex — одиночное нажатие клавиши мода
			net.minecraft.client.KeyMapping key = switch (step.substring(6).strip()) {
				case "cast" -> dev.celestial.client.grace.GraceClient.CAST;
				case "cycle" -> dev.celestial.client.grace.GraceClient.CYCLE;
				case "dash" -> dev.celestial.client.grace.GraceClient.DASH;
				default -> dev.celestial.client.grace.GraceClient.CODEX;
			};
			net.minecraft.client.KeyMapping.click(key.getDefaultKey());
			waitTicks = 3;
		} else if (step.equals("quit")) {
			mc.stop();
		}
	}
}
