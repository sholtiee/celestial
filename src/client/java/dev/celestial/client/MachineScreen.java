package dev.celestial.client;

import dev.celestial.item.RuneItem;
import dev.celestial.network.MachinePayload;
import dev.celestial.registry.ModItems;
import java.util.List;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/**
 * Экран машины (ПКМ пустой рукой по Небесной кузне или Алтарю наделения): состояние (собрана, есть ли питание) и таблица того,
 * что машина делает, с иконками и ценой. Работают машины по-прежнему кликом предметом — экран только объясняет.
 */
public class MachineScreen extends Screen {
	private static final int W = 340, H = 210;  // размер рамки codex.png
	private static final net.minecraft.resources.Identifier BACKGROUND = dev.celestial.Celestial.id("textures/gui/codex.png");
	private final MachinePayload info;

	public MachineScreen(MachinePayload info) {
		super(Component.translatable("machine.celestial.screen." + info.machine()));
		this.info = info;
	}

	public static void register() {
		ClientPlayNetworking.registerGlobalReceiver(MachinePayload.TYPE, (payload, ctx) -> Minecraft.getInstance().gui.setScreen(new MachineScreen(payload)));
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor g, int mx, int my, float a) {
		super.extractRenderState(g, mx, my, a);
		int left = (width - W) / 2, top = (height - H) / 2;
		g.blit(net.minecraft.client.renderer.RenderPipelines.GUI_TEXTURED, BACKGROUND, left, top, 0.0F, 0.0F, W, H, 512, 256);
		g.centeredText(font, title.copy().withStyle(ChatFormatting.GOLD), left + W / 2, top + 10, 0xFFFFFFFF);
		int y = top + 26;
		boolean forge = info.machine().equals("forge");
		if (forge) {
			y = status(g, left + 12, y, info.complete(), "machine.celestial.screen.assembled", "machine.celestial.screen.not_assembled");
		}
		y = status(g, left + 12, y, info.powered(), forge ? "machine.celestial.screen.powered_forge" : "machine.celestial.screen.powered",
			forge ? "machine.celestial.screen.unpowered_forge" : "machine.celestial.screen.unpowered");
		y += 5;
		if (forge) {
			forgeTable(g, left, y, mx, my);
		} else {
			altarTable(g, left, y, mx, my);
		}
	}

	/** Строка состояния с переносом по ширине рамки; возвращает y под ней. */
	private int status(GuiGraphicsExtractor g, int x, int y, boolean ok, String yes, String no) {
		var line = Component.literal(ok ? "✔ " : "✘ ").withStyle(ok ? ChatFormatting.GREEN : ChatFormatting.RED)
			.append(Component.translatable(ok ? yes : no).withStyle(ChatFormatting.GRAY));
		for (var row : font.split(line, W - 24)) {
			g.text(font, row, x, y, 0xFFFFFFFF);
			y += 10;
		}
		return y + 1;
	}

	private static final Item[][] UPGRADES = {
		{Items.DIAMOND_SWORD, ModItems.ETHERITE_SWORD}, {Items.DIAMOND_PICKAXE, ModItems.ETHERITE_PICKAXE}, {Items.DIAMOND_AXE, ModItems.ETHERITE_AXE},
		{Items.DIAMOND_SHOVEL, ModItems.ETHERITE_SHOVEL}, {Items.DIAMOND_HOE, ModItems.ETHERITE_HOE}, {Items.DIAMOND_HELMET, ModItems.ETHERITE_HELMET},
		{Items.DIAMOND_CHESTPLATE, ModItems.ETHERITE_CHESTPLATE}, {Items.DIAMOND_LEGGINGS, ModItems.ETHERITE_LEGGINGS}, {Items.DIAMOND_BOOTS, ModItems.ETHERITE_BOOTS}};

	private void forgeTable(GuiGraphicsExtractor g, int left, int y, int mx, int my) {
		g.text(font, Component.translatable("machine.celestial.screen.upgrade").withStyle(ChatFormatting.AQUA), left + 12, y, 0xFFFFFFFF);
		y += 12;
		ItemStack hovered = ItemStack.EMPTY;
		for (int i = 0; i < UPGRADES.length; i++) {  // три столбца: алмаз → эфирит
			int x = left + 16 + (i % 3) * 104, yy = y + (i / 3) * 19;
			ItemStack from = new ItemStack(UPGRADES[i][0]), to = new ItemStack(UPGRADES[i][1]);
			g.item(from, x, yy);
			g.text(font, Component.literal("→").withStyle(ChatFormatting.GOLD), x + 20, yy + 4, 0xFFFFFFFF);
			g.item(to, x + 30, yy);
			hovered = hover(hovered, from, x, yy, mx, my);
			hovered = hover(hovered, to, x + 30, yy, mx, my);
		}
		y += 60;
		g.text(font, Component.translatable("machine.celestial.screen.cost").withStyle(ChatFormatting.GRAY), left + 12, y + 4, 0xFFFFFFFF);
		int cx = left + 12 + font.width(Component.translatable("machine.celestial.screen.cost")) + 4;
		hovered = costIcon(g, new ItemStack(ModItems.ETHERITE_INGOT, 2), cx, y, mx, my, hovered);
		hovered = costIcon(g, new ItemStack(ModItems.STARQUARTZ, 1), cx + 22, y, mx, my, hovered);
		y += 20;
		g.text(font, Component.translatable("machine.celestial.screen.repair").withStyle(ChatFormatting.AQUA), left + 12, y, 0xFFFFFFFF);
		y += 12;
		hovered = costIcon(g, new ItemStack(ModItems.STARQUARTZ, 1), left + 12, y, mx, my, hovered);
		g.text(font, Component.translatable("machine.celestial.screen.repair_text").withStyle(ChatFormatting.GRAY), left + 34, y + 4, 0xFFFFFFFF);
		g.text(font, Component.translatable("machine.celestial.screen.forge_how").withStyle(ChatFormatting.DARK_GRAY), left + 12, top() + H - 16, 0xFFFFFFFF);
		tooltip(g, hovered, mx, my);
	}

	private void altarTable(GuiGraphicsExtractor g, int left, int y, int mx, int my) {
		g.text(font, Component.translatable("machine.celestial.screen.runes").withStyle(ChatFormatting.AQUA), left + 12, y, 0xFFFFFFFF);
		y += 14;
		ItemStack hovered = ItemStack.EMPTY;
		for (Item item : List.of(ModItems.RUNE_OF_WIND, ModItems.RUNE_OF_LIGHT, ModItems.RUNE_OF_SKY, ModItems.RUNE_OF_STARS)) {
			ItemStack rune = new ItemStack(item);
			g.item(rune, left + 12, y);
			hovered = hover(hovered, rune, left + 12, y, mx, my);
			var line = Component.empty();
			for (String id : ((RuneItem) item).enchantments()) {
				if (!line.getSiblings().isEmpty()) {
					line.append(Component.literal(", ").withStyle(ChatFormatting.DARK_GRAY));
				}
				line.append(Component.translatable("enchantment.celestial." + id).withStyle(ChatFormatting.WHITE));
			}
			g.text(font, rune.getHoverName().copy().withStyle(ChatFormatting.GOLD), left + 34, y, 0xFFFFFFFF);
			g.text(font, line, left + 34, y + 9, 0xFFFFFFFF);
			y += 23;
		}
		g.text(font, Component.translatable("machine.celestial.screen.infusion_cost").withStyle(ChatFormatting.GRAY), left + 12, y + 2, 0xFFFFFFFF);
		g.text(font, Component.translatable("machine.celestial.screen.infusion_how").withStyle(ChatFormatting.DARK_GRAY), left + 12, top() + H - 16, 0xFFFFFFFF);
		tooltip(g, hovered, mx, my);
	}

	private int top() {
		return (height - H) / 2;
	}

	private ItemStack costIcon(GuiGraphicsExtractor g, ItemStack stack, int x, int y, int mx, int my, ItemStack hovered) {
		g.item(stack, x, y);
		g.itemDecorations(font, stack, x, y);
		return hover(hovered, stack, x, y, mx, my);
	}

	private static ItemStack hover(ItemStack current, ItemStack stack, int x, int y, int mx, int my) {
		return mx >= x && mx < x + 16 && my >= y && my < y + 16 ? stack : current;
	}

	private void tooltip(GuiGraphicsExtractor g, ItemStack stack, int mx, int my) {
		if (!stack.isEmpty()) {
			g.setTooltipForNextFrame(font, stack, mx, my);
		}
	}
}
