package dev.celestial.client.grace;

import dev.celestial.client.ClientState;
import dev.celestial.data.PlayerData;
import dev.celestial.grace.GracePayloads;
import dev.celestial.grace.Skill;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;

/** Кодекс Небес: Сага, Благодать (дерево навыков), Бестиарий, Места, Справочник. */
public class CodexScreen extends Screen {
	private enum Tab { SAGA, GRACE, BESTIARY, PLACES, GUIDE, LORE }

	private static final String[] MOBS = {"fallen_guardian", "storm_spirit", "winged_serpent", "cloud_whale", "light_wisp", "angel", "pegasus",
		"cherub", "golden_ram", "sky_ray", "cloud_jelly", "mimic", "storm_elemental", "fallen_seraph", "shadow", "blind_hunter", "light_eater", "deep_worm", "light_devourer", "frost_wraith", "ice_guardian", "ice_wolf", "frost_archon", "inia"};
	private static final String[] PLACES = {"sky_village", "sky_ruins", "trial_tower", "beam_temple", "cloud_castle", "sky_lighthouse",
		"airship_wreck", "citadel", "meteor_crater", "observatory", "flame_sanctuary", "void_rift", "abyss_rift", "abyss", "sunken_temple", "devourer_lair", "frozen_citadel", "mirror_maze", "angel_camp", "memory_shrine", "echo_sanctum"};
	private static final String[] PUZZLES = {"bells", "star_tiles", "riddle", "star_lock", "memory", "echo", "glacier", "mirror_maze"};
	private static final int W = 340, H = 210;
	private static final net.minecraft.resources.Identifier BACKGROUND = dev.celestial.Celestial.id("textures/gui/codex.png");
	private static Tab tab = Tab.SAGA;
	private final List<Component> lines = new ArrayList<>();
	private final List<Button> tabButtons = new ArrayList<>();
	private int scroll;
	private int maxScroll;
	/** Область прокручиваемого текста: x, y, ширина (по умолчанию — вся страница; Летопись сужает её рядом с картинкой). */
	private int[] textArea = new int[3];

	public CodexScreen() {
		super(Component.translatable("codex.celestial.title"));
	}

	/** Открыть Кодекс сразу на вкладке (для автопилота и предметов). */
	public static CodexScreen onTab(String spec) {
		String[] parts = spec.strip().split("\\s+");
		tab = Tab.valueOf(parts[0].toUpperCase(java.util.Locale.ROOT));
		if (tab == Tab.LORE && parts.length > 1) {  // codex lore thread | books [N] | sheet <id> | glossary
			LorePanel.open(parts[1], parts.length > 2 ? parts[2] : null);
		}
		return new CodexScreen();
	}

	private static Component tabLabel(Tab t) {
		return Component.translatable("codex.celestial.tab." + t.name().toLowerCase());
	}

	private static net.minecraft.resources.Identifier tabIcon(Tab t) {
		return dev.celestial.Celestial.id("textures/gui/codex_tab_" + t.name().toLowerCase() + ".png");
	}

	private int left() {
		return (width - W) / 2;
	}

	private int top() {
		return (height - H) / 2;
	}

	@Override
	protected void init() {
		clearWidgets();
		lines.clear();
		tabButtons.clear();
		textArea = new int[] {left() + 8, top() + 32, W - 16};
		int x = left() + 6;
		for (Tab t : Tab.values()) {
			// вкладка — иконка; у открытой рядом ещё и название (иконки рисуем в extractRenderState)
			Component label = tabLabel(t);
			int w = t == tab ? 26 + font.width(label) : 24;
			Button b = Button.builder(Component.empty(), btn -> {
				tab = t;
				scroll = 0;
				init();
			}).bounds(x, top() + 4, w, 20).build();
			b.setTooltip(Tooltip.create(label));
			addRenderableWidget(b);
			tabButtons.add(b);
			x += w + 2;
		}
		PlayerData d = GraceClient.data();
		switch (tab) {
			case SAGA -> {
				lines.add(Component.translatable("codex.celestial.saga.act", ClientState.act()));
				lines.add(Component.translatable("codex.celestial.saga.fading", ClientState.fading()));
				lines.add(Component.translatable("codex.celestial.saga.stats", d.grace(), d.reputation(), d.trials().size(), d.codex().stream().filter(e -> !e.startsWith("beacon:")).count()));
				lines.add(Component.empty());
				lines.add(Component.translatable("codex.celestial.saga.text." + Math.min(ClientState.act(), 3)));
			}
			case GRACE -> buildGrace(d);
			case LORE -> textArea = LorePanel.build(left(), top(), W, d, lines, this::addRenderableWidget, this::init);
			case BESTIARY -> {
				for (String m : MOBS) {
					boolean known = d.knows("mob:" + m);
					lines.add(known ? Component.translatable("entity.celestial." + m).withStyle(ChatFormatting.GOLD)
						.append(Component.literal(" — ").withStyle(ChatFormatting.DARK_GRAY))
						.append(Component.translatable("codex.celestial.mob." + m).withStyle(ChatFormatting.GRAY))
						: Component.literal("???").withStyle(ChatFormatting.DARK_GRAY));
				}
			}
			case PLACES -> {
				for (String p : PLACES) {
					boolean known = d.knows("place:" + p);
					lines.add(known ? Component.translatable("structure.celestial." + p).withStyle(ChatFormatting.AQUA)
						.append(Component.literal(" — ").withStyle(ChatFormatting.DARK_GRAY))
						.append(Component.translatable("codex.celestial.place." + p).withStyle(ChatFormatting.GRAY))
						: Component.literal("???").withStyle(ChatFormatting.DARK_GRAY));
				}
			}
			case GUIDE -> {
				for (int i = 1; i <= 13; i++) {
					lines.add(Component.translatable("codex.celestial.guide." + i));
				}
				// загадки: решённые отмечены, у остальных — подсказка, где искать
				lines.add(Component.empty());
				lines.add(Component.translatable("codex.celestial.puzzles").withStyle(ChatFormatting.LIGHT_PURPLE));
				for (String p : PUZZLES) {
					boolean solved = d.knows("puzzle_" + p);
					lines.add(Component.literal(solved ? "✦ " : "✧ ").withStyle(solved ? ChatFormatting.GOLD : ChatFormatting.DARK_GRAY)
						.append(Component.translatable("codex.celestial.puzzle." + p).withStyle(solved ? ChatFormatting.AQUA : ChatFormatting.GRAY))
						.append(Component.literal(" — ").withStyle(ChatFormatting.DARK_GRAY))
						.append(Component.translatable("codex.celestial.puzzle." + p + ".hint").withStyle(ChatFormatting.GRAY)));
				}
			}
		}
	}

	private void buildGrace(PlayerData d) {
		lines.add(Component.translatable("codex.celestial.grace.points", d.grace()).withStyle(ChatFormatting.GOLD));
		int colW = (W - 12) / 3;
		int longest = 0;
		for (Skill.Branch b : Skill.Branch.values()) {
			longest = Math.max(longest, Skill.branch(b).size());
		}
		int rowH = Math.min(21, (H - 60) / longest);
		for (Skill.Branch branch : Skill.Branch.values()) {
			int bx = left() + 6 + branch.ordinal() * colW;
			int row = 0;
			for (Skill s : Skill.branch(branch)) {
				boolean learned = d.hasSkill(s.id);
				boolean open = s.requires == null || d.hasSkill(s.requires.id);
				Component name = Component.translatable("skill.celestial." + s.id);
				Component label = learned ? Component.literal("✔ ").append(name).withStyle(ChatFormatting.GREEN)
					: open ? name.copy().withStyle(d.grace() >= s.cost ? ChatFormatting.YELLOW : ChatFormatting.WHITE)
					: name.copy().withStyle(ChatFormatting.DARK_GRAY);
				// отступ по глубине — видно, из чего растёт навык
				int indent = depth(s) * 6;
				Button b = Button.builder(label, btn -> {
					ClientPlayNetworking.send(new GracePayloads.LearnSkill(s.id));
					onClose();
				}).bounds(bx + indent, top() + 54 + row * rowH, colW - 4 - indent, rowH - 2).build();
				var tip = Component.translatable("skill.celestial." + s.id + ".desc").copy()
					.append(Component.literal("\n")).append(Component.translatable("codex.celestial.grace.cost", s.cost).withStyle(ChatFormatting.GOLD));
				if (s.requires != null) {
					tip.append(Component.literal("\n")).append(Component.translatable("codex.celestial.grace.requires",
						Component.translatable("skill.celestial." + s.requires.id)).withStyle(ChatFormatting.GRAY));
				}
				b.setTooltip(Tooltip.create(tip));
				b.active = !learned && open;
				addRenderableWidget(b);
				row++;
			}
		}
	}

	private static int depth(Skill s) {
		return s.requires == null ? 0 : 1 + depth(s.requires);
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float a) {
		graphics.blit(net.minecraft.client.renderer.RenderPipelines.GUI_TEXTURED, BACKGROUND, left(), top(), 0.0F, 0.0F, W, H, 512, 256);
		super.extractRenderState(graphics, mouseX, mouseY, a);
		Tab[] tabs = Tab.values();
		for (int i = 0; i < tabs.length && i < tabButtons.size(); i++) {
			Button b = tabButtons.get(i);
			graphics.blit(net.minecraft.client.renderer.RenderPipelines.GUI_TEXTURED, tabIcon(tabs[i]), b.getX() + 4, b.getY() + 2, 0.0F, 0.0F, 16, 16, 16, 16);
			if (tabs[i] == tab) {
				graphics.text(font, tabLabel(tabs[i]).copy().withStyle(ChatFormatting.GOLD), b.getX() + 22, b.getY() + 6, 0xFFFFFFFF);
				graphics.fill(b.getX() + 2, b.getY() + 19, b.getX() + b.getWidth() - 2, b.getY() + 20, 0xFFC9A23A);
			}
		}
		if (tab == Tab.LORE) {
			LorePanel.render(graphics, font, left(), top(), W, GraceClient.data());
		}
		int y = textArea[1];
		if (tab == Tab.GRACE) {
			for (Skill.Branch b : Skill.Branch.values()) {
				graphics.text(font, Component.translatable("codex.celestial.branch." + b.name().toLowerCase()).withStyle(ChatFormatting.AQUA),
					left() + 8 + b.ordinal() * ((W - 12) / 3), top() + 43, 0xFFFFFFFF);
			}
		}
		// длинные вкладки (бестиарий, справочник) прокручиваются колесом мыши
		List<FormattedCharSequence> rows = new ArrayList<>();
		for (Component line : lines) {
			rows.addAll(font.split(line, textArea[2]));
		}
		int visible = (top() + H - 12 - y) / 10;
		maxScroll = Math.max(0, rows.size() - visible);
		scroll = Math.min(scroll, maxScroll);
		for (int i = scroll; i < rows.size() && i < scroll + visible; i++) {
			graphics.text(font, rows.get(i), textArea[0], y, 0xFFFFFFFF);
			y += 10;
		}
		if (maxScroll > 0) {  // полоса прокрутки у правого края
			int trackTop = top() + 32, trackH = H - 44;
			int thumbH = Math.max(12, trackH * visible / rows.size());
			int thumbY = trackTop + (trackH - thumbH) * scroll / maxScroll;
			graphics.fill(left() + W - 7, trackTop, left() + W - 5, trackTop + trackH, 0x60C9A23A);
			graphics.fill(left() + W - 7, thumbY, left() + W - 5, thumbY + thumbH, 0xFFC9A23A);
		}
	}

	@Override
	public boolean mouseScrolled(double x, double y, double scrollX, double scrollY) {
		scroll = Math.max(0, Math.min(maxScroll, scroll - (int) Math.signum(scrollY) * 2));
		return true;
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}
}
