package dev.celestial.client.grace;

import dev.celestial.astral.Choir;
import dev.celestial.astral.Choirs;
import dev.celestial.data.PlayerData;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.network.chat.Component;

/**
 * Вкладка Кодекса «Созвездия»: ранг и покровитель сверху, ниже — девять карточек хоров (3×3). На карточке — рисунок созвездия
 * (точки и линии на поле 5×5, верх — север, как на Звёздном диске), имя и состояние: собран ✦ / видел в Телескоп / не видел.
 * Невиденное созвездие — пустая рамка с фазой Луны, когда его искать. Подсказка при наведении — благословение хора.
 */
public final class StarsPanel {
	private static final int CARD_H = 50;
	private static final int CELL = 6;

	private StarsPanel() {}

	/** Строки над карточками; возвращает область текста (x, y, ширина). */
	public static int[] build(int left, int top, int w, PlayerData d, List<Component> lines) {
		int rank = Choirs.rank(d);
		lines.add(Component.translatable("codex.celestial.stars.rank", Component.translatable("rank.celestial." + rank).withStyle(ChatFormatting.GOLD),
			Choirs.count(d)).withStyle(ChatFormatting.GRAY));
		Choir patron = Choirs.patron(d);
		lines.add(patron == null ? Component.translatable("codex.celestial.stars.no_patron").withStyle(ChatFormatting.DARK_GRAY)
			: Component.translatable("codex.celestial.stars.patron", Component.translatable("choir.celestial." + patron.id).withStyle(ChatFormatting.AQUA),
				Component.translatable("choir.celestial." + patron.id + ".blessing")).withStyle(ChatFormatting.GRAY));
		return new int[] {left + 8, top + 30, w - 16};
	}

	public static void render(GuiGraphicsExtractor g, Font font, int left, int top, int w, int h, PlayerData d, int mx, int my) {
		int cw = (w - 16) / 3;
		int y0 = top + 54;
		Choir patron = Choirs.patron(d);
		for (Choir c : Choir.values()) {
			int i = c.ordinal();
			int x = left + 8 + (i % 3) * cw;
			int y = y0 + (i / 3) * CARD_H;
			boolean seen = d.knows("constellation:" + c.id);
			boolean got = Choirs.collected(d, c);
			int frame = got ? 0xFFC9A23A : seen ? 0xFF5A7AC8 : 0xFF3A3A50;
			g.fill(x, y, x + cw - 4, y + CARD_H - 4, 0x90080A1C);
			g.fill(x, y, x + cw - 4, y + 1, frame);
			g.fill(x, y + CARD_H - 5, x + cw - 4, y + CARD_H - 4, frame);
			g.fill(x, y, x + 1, y + CARD_H - 4, frame);
			g.fill(x + cw - 5, y, x + cw - 4, y + CARD_H - 4, frame);
			int ox = x + 5 + 2 * CELL, oy = y + 15 + 2 * CELL;  // центр поля 5×5 (под именем, слева)
			if (seen || got) {
				for (int[] ln : c.lines) {
					int[] a = c.points[ln[0]], b = c.points[ln[1]];
					line(g, ox + a[0] * CELL, oy + a[1] * CELL, ox + b[0] * CELL, oy + b[1] * CELL, got ? 0xFF8A9AE0 : 0xFF4A5A90);
				}
				for (int[] p : c.points) {
					int px = ox + p[0] * CELL, py = oy + p[1] * CELL;
					g.fill(px - 1, py - 1, px + 2, py + 2, got ? 0xFFFFF1B8 : 0xFFB8C8FF);
				}
			} else {
				for (int gx = -2; gx <= 2; gx++) {
					for (int gz = -2; gz <= 2; gz++) {
						g.fill(ox + gx * CELL, oy + gz * CELL, ox + gx * CELL + 1, oy + gz * CELL + 1, 0xFF2A2A40);
					}
				}
			}
			Component name = seen || got ? Component.translatable("choir.celestial." + c.id).copy().append(c == patron ? " ✦" : "")
				: Component.literal("???");
			g.text(font, name.copy().withStyle(got ? ChatFormatting.GOLD : seen ? ChatFormatting.AQUA : ChatFormatting.DARK_GRAY), x + 4, y + 4, 0xFFFFFFFF);
			int tx = x + 4 + 4 * CELL + 7;
			Component state = got ? Component.translatable(c == patron ? "codex.celestial.stars.is_patron" : "codex.celestial.stars.collected")
				: seen ? Component.translatable("codex.celestial.stars.seen")
				: Component.translatable(c.moonPhase < 0 ? "codex.celestial.stars.astral_only" : "codex.celestial.stars.phase." + c.moonPhase);
			List<net.minecraft.util.FormattedCharSequence> rows = font.split(state.copy().withStyle(ChatFormatting.GRAY), cw - (tx - x) - 5);
			for (int r = 0; r < rows.size() && r < 3; r++) {
				g.text(font, rows.get(r), tx, y + 16 + r * 9, 0xFFFFFFFF);
			}
			if (mx >= x && mx < x + cw - 4 && my >= y && my < y + CARD_H - 4 && (seen || got)) {
				List<net.minecraft.util.FormattedCharSequence> tip = new ArrayList<>();
				tip.addAll(font.split(Component.translatable("choir.celestial." + c.id).withStyle(ChatFormatting.GOLD), 200));
				tip.addAll(font.split(Component.translatable("choir.celestial." + c.id + ".blessing").withStyle(ChatFormatting.GRAY), 200));
				g.setTooltipForNextFrame(tip, mx, my);
			}
		}
	}

	private static void line(GuiGraphicsExtractor g, int x0, int y0, int x1, int y1, int color) {
		int n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0));
		for (int k = 0; k <= n; k += 2) {  // пунктир — как линии на звёздной карте
			int x = x0 + (x1 - x0) * k / Math.max(1, n);
			int y = y0 + (y1 - y0) * k / Math.max(1, n);
			g.fill(x, y, x + 1, y + 1, color);
		}
	}
}
