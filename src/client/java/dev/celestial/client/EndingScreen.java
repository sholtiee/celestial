package dev.celestial.client;

import dev.celestial.network.EndingPayloads;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/**
 * Выбор концовки у повергнутого Безликого: «Возжечь», «Поглотить» и тайное «Имя» (недоступно без всей Летописи — серая кнопка
 * с подсказкой). Над кнопками — его слова; выбор необратим.
 */
public class EndingScreen extends Screen {
	private final boolean nameAllowed;

	public EndingScreen(boolean nameAllowed) {
		super(Component.translatable("ending.celestial.screen.title"));
		this.nameAllowed = nameAllowed;
	}

	public static void register() {
		ClientPlayNetworking.registerGlobalReceiver(EndingPayloads.Open.TYPE,
			(payload, ctx) -> Minecraft.getInstance().gui.setScreen(new EndingScreen(payload.nameAllowed())));
	}

	@Override
	protected void init() {
		int w = 220, x = width / 2 - w / 2, y = height / 2 - 10;
		add(x, y, w, "kindle", true);
		add(x, y + 26, w, "consume", true);
		add(x, y + 52, w, "name", nameAllowed);
	}

	private void add(int x, int y, int w, String choice, boolean active) {
		Button b = Button.builder(Component.translatable("ending.celestial.choice." + choice), btn -> {
			if (choice.equals("name")) {
				Minecraft.getInstance().gui.setScreen(new NameScreen());  // имя складывают по буквам
				return;
			}
			ClientPlayNetworking.send(new EndingPayloads.Choose(choice));
			onClose();
		}).bounds(x, y, w, 20).build();
		b.setTooltip(Tooltip.create(Component.translatable(active ? "ending.celestial.choice." + choice + ".desc" : "ending.celestial.name.locked")));
		b.active = active;
		addRenderableWidget(b);
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor g, int mx, int my, float a) {
		g.fill(0, 0, width, height, 0xC0050510);
		super.extractRenderState(g, mx, my, a);
		g.centeredText(font, title.copy().withStyle(ChatFormatting.GOLD), width / 2, height / 2 - 70, 0xFFFFFFFF);
		var rows = font.split(Component.translatable("ending.celestial.screen.text").withStyle(ChatFormatting.GRAY), 300);
		for (int i = 0; i < rows.size(); i++) {
			g.centeredText(font, rows.get(i), width / 2, height / 2 - 52 + i * 10, 0xFFFFFFFF);
		}
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}
}
