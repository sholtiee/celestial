package dev.celestial.client.grace;

import dev.celestial.Celestial;
import dev.celestial.client.ClientState;
import dev.celestial.data.PlayerData;
import dev.celestial.lore.Lore;
import java.util.List;
import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;

/**
 * Вкладка Кодекса «Летопись» (docs/LORE.md): лента «Нить», книги с листами и Глоссарий. Лист — картинка-кадр и 1–3 короткие
 * записи («Писание», «Апокриф Небес», «Предание»): это дневник пережитого, а не учебник. Состояние (вид, книга, лист) хранится между
 * открытиями Кодекса, как и вкладка.
 */
public final class LorePanel {
	enum View { THREAD, BOOKS, GLOSSARY }

	static View view = View.THREAD;
	static int book = 1;
	static String sheet;

	private static final int SUB_Y = 28;
	private static final int ART_W = 96, ART_H = 54;
	private static final int[] NODE_COLORS = {0xFF3A3048, 0xFFFFD27F};

	private LorePanel() {}

	/** Для автопилота: открыть Летопись сразу на нужном виде. */
	static void open(String viewName, String arg) {
		sheet = null;
		switch (viewName) {
			case "books" -> {
				view = View.BOOKS;
				if (arg != null) {
					book = Integer.parseInt(arg);
				}
			}
			case "sheet" -> {
				view = View.BOOKS;
				Lore.sheet(arg).ifPresent(s -> {
					book = s.book();
					if (dev.celestial.client.grace.GraceClient.data().knowsLore(s.id())) {  // закрытый лист не показываем
						sheet = s.id();
					}
				});
			}
			case "glossary" -> view = View.GLOSSARY;
			default -> view = View.THREAD;
		}
	}

	/** Сервер просит показать лист (после чтения свитка/скрижали): открываем Кодекс на нём без проверки синхронизации данных. */
	public static void initNetwork() {
		net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking.registerGlobalReceiver(dev.celestial.network.OpenLorePayload.TYPE, (payload, context) ->
			context.client().execute(() -> {
				view = View.BOOKS;
				sheet = payload.sheet();
				Lore.sheet(payload.sheet()).ifPresent(s -> book = s.book());
				context.client().gui.setScreen(CodexScreen.onTab("lore"));
			}));
	}

	private static Identifier art(String name) {
		return Celestial.id("textures/gui/lore/" + name + ".png");
	}

	/** Кнопки вкладки и строки текста (Глоссарий, лист). Возвращает область текста {x, y, ширина}. */
	static int[] build(int left, int top, int w, PlayerData d, List<Component> lines, Consumer<Button> add, Runnable rebuild) {
		int x = left + 6;
		for (View v : View.values()) {
			Component label = Component.translatable("lore.celestial.view." + v.name().toLowerCase());
			Button b = Button.builder(v == view ? label.copy().withStyle(ChatFormatting.GOLD) : label, btn -> {
				view = v;
				sheet = null;
				rebuild.run();
			}).bounds(x, top + SUB_Y, 74, 16).build();
			add.accept(b);
			x += 76;
		}
		int[] area = {left + 8, top + 32, w - 16};
		switch (view) {
			case THREAD -> buildThread(left, top, w, d, add, rebuild);
			case BOOKS -> {
				if (sheet != null) {
					area = buildSheet(left, top, w, d, lines, add, rebuild);
				} else {
					buildBooks(left, top, d, add, rebuild);
				}
			}
			case GLOSSARY -> {
				area = new int[] {left + 8, top + 50, w - 16};
				boolean any = false;
				for (String g : Lore.glossary()) {
					if (!Lore.glossaryKnown(d, g)) {
						continue;
					}
					any = true;
					lines.add(Component.translatable("lore.celestial.gloss." + g).withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD)
						.append(Component.literal(" — ").withStyle(ChatFormatting.DARK_GRAY))
						.append(Component.translatable("lore.celestial.gloss." + g + ".who").withStyle(ChatFormatting.WHITE)));
					lines.add(Component.translatable("lore.celestial.gloss.here").withStyle(ChatFormatting.GOLD)
						.append(Component.translatable("lore.celestial.gloss." + g + ".here").withStyle(ChatFormatting.GRAY)));
				}
				if (!any) {
					lines.add(Component.translatable("lore.celestial.gloss.empty").withStyle(ChatFormatting.DARK_GRAY));
				}
			}
		}
		return area;
	}

	// ------------------------------------------------------------------ Нить
	private static int nodeX(int left, int w, int i) {
		return left + 22 + i * (w - 44) / (Lore.nodes().size() - 1);
	}

	private static void buildThread(int left, int top, int w, PlayerData d, Consumer<Button> add, Runnable rebuild) {
		List<Lore.Node> nodes = Lore.nodes();
		for (int i = 0; i < nodes.size(); i++) {
			Lore.Node n = nodes.get(i);
			long open = Lore.openInNode(d, n.id());
			long total = Lore.totalInNode(n.id());
			Component name = Component.translatable("lore.celestial.node." + n.id());
			Component tip = total == 0 ? name.copy().append(Component.literal("\n")).append(Component.translatable("lore.celestial.soon").withStyle(ChatFormatting.GRAY))
				: Component.translatable("lore.celestial.thread.node", name, open, total);
			Button b = Button.builder(Component.empty(), btn -> {
				Lore.sheets().stream().filter(s -> s.node().equals(n.id())).findFirst().ifPresent(s -> {
					view = View.BOOKS;
					book = s.book();
					sheet = null;
					rebuild.run();
				});
			}).bounds(nodeX(left, w, i) - 10, top + 90, 20, 20).build();
			b.setTooltip(Tooltip.create(tip));
			add.accept(b);
		}
	}

	private static void renderThread(GuiGraphicsExtractor g, Font font, int left, int top, int w, PlayerData d) {
		List<Lore.Node> nodes = Lore.nodes();
		int y = top + 100;
		int x0 = nodeX(left, w, 0), x1 = nodeX(left, w, nodes.size() - 1);
		g.fill(x0, y - 1, x1, y + 1, 0xFF3A3048);
		int lastLit = -1;
		for (int i = 0; i < nodes.size(); i++) {
			if (Lore.openInNode(d, nodes.get(i).id()) > 0) {
				lastLit = i;
			}
		}
		if (lastLit >= 0) {
			g.fill(x0, y - 1, nodeX(left, w, lastLit), y + 1, 0xFFC9A23A);
		}
		int playing = ClientState.act() + 1;  // акт, который игрок сейчас проходит
		for (int i = 0; i < nodes.size(); i++) {
			Lore.Node n = nodes.get(i);
			int cx = nodeX(left, w, i);
			boolean lit = Lore.openInNode(d, n.id()) > 0;
			int c = NODE_COLORS[lit ? 1 : 0];
			g.fill(cx - 4, y - 4, cx + 4, y + 4, c);
			g.fill(cx - 2, y - 6, cx + 2, y + 6, c);
			g.fill(cx - 6, y - 2, cx + 6, y + 2, c);
			if (lit) {
				g.fill(cx - 1, y - 1, cx + 1, y + 1, 0xFFFFFFFF);
			}
			Component label = Component.translatable("lore.celestial.node." + n.id());
			int half = font.width(label) / 2;
			int lx = Math.max(left + 8 + half, Math.min(left + w - 8 - half, cx));  // подпись не вылезает за рамку Кодекса
			// подписи через одну сверху и снизу; у последнего (длинное «Откровение») — вторая строка снизу, чтобы не слипалось с соседом
			int ly = i % 2 == 0 ? top + 74 : i == nodes.size() - 1 ? top + 130 : top + 118;
			g.centeredText(font, label, lx, ly, lit ? 0xFFFFE9A0 : 0xFF7A7A90);
			if (n.act() > 0) {
				boolean reached = ClientState.act() >= n.act();
				boolean here = playing == n.act();
				g.centeredText(font, roman(n.act()), cx, top + 148, reached ? 0xFFFFD27F : here ? 0xFFFFFFFF : 0xFF5A5A70);
				if (here) {
					g.fill(cx - 8, top + 158, cx + 8, top + 159, 0xFFFFE9A0);
				}
			}
		}
		g.text(font, Component.translatable("lore.celestial.thread.acts"), left + 8, top + 148, 0xFF8A8AA0);
		g.centeredText(font, Component.translatable("lore.celestial.thread.hint").withStyle(ChatFormatting.ITALIC), left + w / 2, top + 186, 0xFF8A8AA0);
	}

	private static String roman(int n) {
		return new String[] {"", "I", "II", "III", "IV", "V"}[Math.max(0, Math.min(5, n))];
	}

	// ------------------------------------------------------------------ Книги и листы
	private static void buildBooks(int left, int top, PlayerData d, Consumer<Button> add, Runnable rebuild) {
		int row = 0;
		for (int n : Lore.books()) {
			long total = Lore.sheetsOfBook(n).size();
			Component name = Component.translatable("lore.celestial.book." + n);
			Component label = total == 0 ? name.copy().withStyle(ChatFormatting.DARK_GRAY)
				: name.copy().append(Component.literal("  " + Lore.openInBook(d, n) + "/" + total).withStyle(ChatFormatting.GRAY));
			Button b = Button.builder(n == book ? label.copy().withStyle(ChatFormatting.GOLD) : label, btn -> {
				book = n;
				rebuild.run();
			}).bounds(left + 6, top + 50 + row * 20, 124, 18).build();
			if (total == 0) {
				b.setTooltip(Tooltip.create(Component.translatable("lore.celestial.soon")));
			}
			add.accept(b);
			row++;
		}
		row = 0;
		for (Lore.Sheet s : Lore.sheetsOfBook(book)) {
			boolean open = d.knowsLore(s.id());
			Component label = open ? Component.translatable("lore.celestial.sheet." + s.id() + ".title").withStyle(ChatFormatting.AQUA)
				: Component.literal("???").withStyle(ChatFormatting.DARK_GRAY);
			Button b = Button.builder(label, btn -> {
				if (open) {
					sheet = s.id();
					rebuild.run();
				}
			}).bounds(left + 136, top + 50 + row * 16, 192, 15).build();
			b.setTooltip(Tooltip.create(open ? Component.translatable("lore.celestial.sheet." + s.id() + ".title")
				: Component.translatable("lore.celestial.how", Component.translatable("lore.celestial.sheet." + s.id() + ".how")).withStyle(ChatFormatting.GRAY)));
			add.accept(b);
			row++;
		}
	}

	private static int[] buildSheet(int left, int top, int w, PlayerData d, List<Component> lines, Consumer<Button> add, Runnable rebuild) {
		Lore.Sheet s = Lore.sheet(sheet).orElseThrow();
		String p = "lore.celestial.sheet." + s.id();
		lines.add(Component.translatable(p + ".title").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
		lines.add(Component.translatable(p + ".ref").withStyle(ChatFormatting.GRAY));
		if (s.quote()) {
			lines.add(Component.translatable(p + ".quote").withStyle(ChatFormatting.ITALIC, ChatFormatting.WHITE));
		}
		lines.add(Component.literal(" "));
		addKind(lines, s.scripture(), "s", p, ChatFormatting.AQUA);
		addKind(lines, s.tradition(), "t", p, ChatFormatting.YELLOW);  // сначала Писание и предание, потом наш вымысел (LORE §1.3)
		addKind(lines, s.apocrypha(), "a", p, ChatFormatting.LIGHT_PURPLE);
		Button back = Button.builder(Component.translatable("lore.celestial.back"), btn -> {
			sheet = null;
			rebuild.run();
		}).bounds(left + 10, top + H_BACK, ART_W, 16).build();
		add.accept(back);
		return new int[] {left + 116, top + 52, w - 130};
	}

	private static final int H_BACK = 190;

	private static void addKind(List<Component> lines, boolean present, String key, String prefix, ChatFormatting colour) {
		if (!present) {
			return;
		}
		lines.add(Component.translatable("lore.celestial.kind." + key).withStyle(colour, ChatFormatting.BOLD));
		lines.add(Component.translatable(prefix + "." + key).withStyle(ChatFormatting.WHITE));
		lines.add(Component.literal(" "));
	}

	private static void renderSheet(GuiGraphicsExtractor g, Font font, int left, int top, PlayerData d) {
		Lore.Sheet s = Lore.sheet(sheet).orElseThrow();
		g.blit(RenderPipelines.GUI_TEXTURED, art(s.art()), left + 10, top + 52, 0.0F, 0.0F, ART_W, ART_H, ART_W, ART_H);
		int y = top + 52 + ART_H + 6;
		if (!s.gloss().isEmpty()) {
			for (String gl : s.gloss()) {
				g.text(font, Component.literal("✦ ").withStyle(ChatFormatting.GOLD).append(Component.translatable("lore.celestial.gloss." + gl).withStyle(ChatFormatting.AQUA)), left + 10, y, 0xFFFFFFFF);
				y += 10;
			}
		}
	}

	/** Рисуется поверх кнопок вкладки (картинка листа, самоцветы «Нити», пустая книга). */
	static void render(GuiGraphicsExtractor g, Font font, int left, int top, int w, PlayerData d) {
		switch (view) {
			case THREAD -> renderThread(g, font, left, top, w, d);
			case BOOKS -> {
				if (sheet != null) {
					renderSheet(g, font, left, top, d);
				} else if (Lore.sheetsOfBook(book).isEmpty()) {
					g.centeredText(font, Component.translatable("lore.celestial.soon").withStyle(ChatFormatting.ITALIC), left + 232, top + 110, 0xFF7A7A90);
				}
			}
			case GLOSSARY -> { }
		}
	}
}
