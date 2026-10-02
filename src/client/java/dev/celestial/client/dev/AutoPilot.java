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

	private static void tick(Minecraft mc) {
		if (mc.player == null || mc.getConnection() == null || steps.isEmpty()) {
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
		} else if (step.equals("pos")) {
			Celestial.LOGGER.info("Автопилот: позиция {} {} {} {} блок-под-ногами={}", mc.player.level().dimension().identifier(),
				(int) Math.floor(mc.player.getX()), (int) Math.floor(mc.player.getY()), (int) Math.floor(mc.player.getZ()),
				mc.player.level().getBlockState(mc.player.blockPosition()).getBlock());
		} else if (step.equals("quit")) {
			mc.stop();
		}
	}
}
