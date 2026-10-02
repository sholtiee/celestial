package dev.celestial.item;

import dev.celestial.story.Story;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.Filterable;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.WrittenBookContent;
import net.minecraft.world.level.Level;

/** Дневник Странника: страницы появляются по мере прохождения глав сюжета. */
public class WandererJournalItem extends Item {
	public WandererJournalItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		if (player instanceof ServerPlayer serverPlayer) {
			stack.set(DataComponents.WRITTEN_BOOK_CONTENT, pagesFor(serverPlayer));
			// сначала синхронизируем страницы с клиентом, иначе он откроет «пустую» книгу
			serverPlayer.containerMenu.broadcastChanges();
			serverPlayer.openItemGui(stack, hand);
		}
		return InteractionResult.SUCCESS;
	}

	private static WrittenBookContent pagesFor(ServerPlayer player) {
		List<Filterable<Component>> pages = new ArrayList<>();
		page(pages, "intro");
		page(pages, "task_flame");
		if (Story.FLAME.isDone(player)) {
			page(pages, "flame");
			page(pages, "task_void");
		}
		if (Story.VOID.isDone(player)) {
			page(pages, "void");
			page(pages, "task_gates");
		}
		if (Story.GATES.isDone(player)) {
			page(pages, "gates");
			page(pages, "task_seraph");
		}
		if (Story.SERAPH.isDone(player)) {
			page(pages, "seraph");
			page(pages, "task_altar");
		}
		if (Story.FINALE.isDone(player)) {
			page(pages, "finale");
		}
		return new WrittenBookContent(Filterable.passThrough("Дневник Странника"), "Странник", 0, pages, true);
	}

	private static void page(List<Filterable<Component>> pages, String key) {
		pages.add(Filterable.passThrough(Component.translatable("journal.celestial." + key)));
	}
}
