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
	private enum Tab { SAGA, GRACE, BESTIARY, PLACES, GUIDE }

	private static final String[] MOBS = {"fallen_guardian", "storm_spirit", "winged_serpent", "cloud_whale", "light_wisp", "angel", "pegasus",
		"cherub", "golden_ram", "sky_ray", "cloud_jelly", "mimic", "storm_elemental", "fallen_seraph", "shadow"};
	private static final String[] PLACES = {"sky_village", "sky_ruins", "trial_tower", "beam_temple", "cloud_castle", "sky_lighthouse",
		"airship_wreck", "citadel", "meteor_crater", "observatory", "flame_sanctuary", "void_rift", "abyss_rift", "abyss"};
	private static final int W = 340, H = 210;
	private static Tab tab = Tab.SAGA;
	private final List<Component> lines = new ArrayList<>();

	public CodexScreen() {
		super(Component.translatable("codex.celestial.title"));
	}

	/** Открыть Кодекс сразу на вкладке (для автопилота и предметов). */
	public static CodexScreen onTab(String name) {
		tab = Tab.valueOf(name.toUpperCase(java.util.Locale.ROOT));
		return new CodexScreen();
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
		int x = left() + 6;
		for (Tab t : Tab.values()) {
			Component label = Component.translatable("codex.celestial.tab." + t.name().toLowerCase());
			Button b = Button.builder(t == tab ? label.copy().withStyle(ChatFormatting.GOLD) : label, btn -> {
				tab = t;
				init();
			}).bounds(x, top() + 6, 64, 18).build();
			addRenderableWidget(b);
			x += 66;
		}
		PlayerData d = GraceClient.data();
		switch (tab) {
			case SAGA -> {
				lines.add(Component.translatable("codex.celestial.saga.act", ClientState.act()));
				lines.add(Component.translatable("codex.celestial.saga.fading", ClientState.fading()));
				lines.add(Component.translatable("codex.celestial.saga.stats", d.grace(), d.reputation(), d.trials().size(), d.codex().size()));
				lines.add(Component.empty());
				lines.add(Component.translatable("codex.celestial.saga.text." + Math.min(ClientState.act(), 1)));
			}
			case GRACE -> buildGrace(d);
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
				for (int i = 1; i <= 9; i++) {
					lines.add(Component.translatable("codex.celestial.guide." + i));
				}
			}
		}
	}

	private void buildGrace(PlayerData d) {
		lines.add(Component.translatable("codex.celestial.grace.points", d.grace()).withStyle(ChatFormatting.GOLD));
		int colW = (W - 12) / 3;
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
				}).bounds(bx + indent, top() + 54 + row * 21, colW - 4 - indent, 19).build();
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
		graphics.fill(left(), top(), left() + W, top() + H, 0xE0141A30);
		graphics.fill(left(), top(), left() + W, top() + 1, 0xFFC9A23A);
		graphics.fill(left(), top() + H - 1, left() + W, top() + H, 0xFFC9A23A);
		super.extractRenderState(graphics, mouseX, mouseY, a);
		int y = top() + 32;
		if (tab == Tab.GRACE) {
			for (Skill.Branch b : Skill.Branch.values()) {
				graphics.text(font, Component.translatable("codex.celestial.branch." + b.name().toLowerCase()).withStyle(ChatFormatting.AQUA),
					left() + 8 + b.ordinal() * ((W - 12) / 3), top() + 43, 0xFFFFFFFF);
			}
		}
		for (Component line : lines) {
			for (FormattedCharSequence part : font.split(line, W - 16)) {
				if (y > top() + H - 12) {
					return;
				}
				graphics.text(font, part, left() + 8, y, 0xFFFFFFFF);
				y += 10;
			}
		}
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}
}
