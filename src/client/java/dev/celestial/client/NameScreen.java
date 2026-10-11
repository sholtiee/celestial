package dev.celestial.client;

import dev.celestial.client.grace.GraceClient;
import dev.celestial.network.EndingPayloads;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/**
 * Тайная концовка: сложить прежнее имя Безликого из семи букв — по букве за каждую полную книгу Летописи (буквы на языке игрока:
 * «Денница» / «Lucifer»). Плитки перемешаны; клик ставит букву в строку, «Стереть» — начать заново, «Назвать» — сказать имя.
 * Порядок книг уходит на сервер, он и проверяет.
 */
public class NameScreen extends Screen {
	/** Перемешанный, но всегда один и тот же порядок плиток (загадка, а не лотерея). */
	private static final int[] ORDER = {5, 2, 7, 1, 4, 6, 3};
	private final List<Integer> picked = new ArrayList<>();
	private final List<Button> tiles = new ArrayList<>();
	private Button speak;

	public NameScreen() {
		super(Component.translatable("ending.celestial.name.screen"));
	}

	@Override
	protected void init() {
		tiles.clear();
		int size = 26, gap = 6;
		int x0 = width / 2 - (ORDER.length * (size + gap) - gap) / 2;
		int y = height / 2;
		for (int i = 0; i < ORDER.length; i++) {
			int book = ORDER[i];
			boolean have = GraceClient.data().knows("letter:" + book);
			Button b = Button.builder(have ? Component.translatable("letter.celestial." + book) : Component.literal("?"), btn -> {
				picked.add(book);
				refresh();
			}).bounds(x0 + i * (size + gap), y, size, 20).build();
			b.active = have;
			addRenderableWidget(b);
			tiles.add(b);
		}
		addRenderableWidget(Button.builder(Component.translatable("ending.celestial.name.clear"), btn -> {
			picked.clear();
			refresh();
		}).bounds(width / 2 - 104, y + 34, 100, 20).build());
		speak = addRenderableWidget(Button.builder(Component.translatable("ending.celestial.name.speak"), btn -> {
			StringBuilder seq = new StringBuilder();
			picked.forEach(seq::append);
			ClientPlayNetworking.send(new EndingPayloads.Choose("name:" + seq));
			onClose();
		}).bounds(width / 2 + 4, y + 34, 100, 20).build());
		refresh();
	}

	private void refresh() {
		for (int i = 0; i < tiles.size(); i++) {
			tiles.get(i).active = GraceClient.data().knows("letter:" + ORDER[i]) && !picked.contains(ORDER[i]);
		}
		if (speak != null) {
			speak.active = picked.size() == ORDER.length;
		}
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor g, int mx, int my, float a) {
		g.fill(0, 0, width, height, 0xD0050510);
		super.extractRenderState(g, mx, my, a);
		g.centeredText(font, title.copy().withStyle(ChatFormatting.GOLD), width / 2, height / 2 - 60, 0xFFFFFFFF);
		var rows = font.split(Component.translatable("ending.celestial.name.screen_text").withStyle(ChatFormatting.GRAY), 300);
		for (int i = 0; i < rows.size(); i++) {
			g.centeredText(font, rows.get(i), width / 2, height / 2 - 46 + i * 10, 0xFFFFFFFF);
		}
		Component word = Component.empty();
		for (int book : picked) {
			word = word.copy().append(Component.translatable("letter.celestial." + book)).append(" ");
		}
		g.centeredText(font, word.copy().withStyle(ChatFormatting.WHITE, ChatFormatting.BOLD), width / 2, height / 2 - 16, 0xFFFFFFFF);
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}
}
