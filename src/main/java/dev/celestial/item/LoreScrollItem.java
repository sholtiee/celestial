package dev.celestial.item;

import dev.celestial.lore.Lore;
import dev.celestial.network.OpenLorePayload;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.Level;

/**
 * Свиток Летописи: в `custom_data` лежит `{sheet:"<id листа>"}`. ПКМ открывает лист в Летописи (свиток тратится, если лист был новым)
 * и показывает его в Кодексе. Свитки хранят только детали (имена, родословные): основное в Летописи приходит прожитыми эпизодами.
 */
public class LoreScrollItem extends Item {
	public LoreScrollItem(Properties properties) {
		super(properties);
	}

	public static ItemStack of(Item item, String sheet) {
		ItemStack stack = new ItemStack(item);
		net.minecraft.nbt.CompoundTag tag = new net.minecraft.nbt.CompoundTag();
		tag.putString("sheet", sheet);
		stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
		return stack;
	}

	public static String sheetOf(ItemStack stack) {
		CustomData data = stack.get(DataComponents.CUSTOM_DATA);
		return data == null ? "" : data.copyTag().getStringOr("sheet", "");
	}

	@Override
	public Component getName(ItemStack stack) {
		String id = sheetOf(stack);
		return Lore.sheet(id).isPresent()
			? Component.translatable("item.celestial.lore_scroll.named", Component.translatable("lore.celestial.sheet." + id + ".title"))
			: Component.translatable("item.celestial.lore_scroll");
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		if (player instanceof ServerPlayer sp) {
			String id = sheetOf(stack);
			if (Lore.sheet(id).isEmpty()) {
				sp.sendOverlayMessage(Component.translatable("lore.celestial.scroll.blank"));
				return InteractionResult.FAIL;
			}
			if (Lore.unlock(sp, id) && !sp.isCreative()) {
				stack.shrink(1);
			} else if (CelestialDataKnown.known(sp, id)) {
				sp.sendOverlayMessage(Component.translatable("lore.celestial.scroll.known"));
			}
			ServerPlayNetworking.send(sp, new OpenLorePayload(id));
		}
		return InteractionResult.SUCCESS;
	}

	/** Маленькая обёртка, чтобы не тянуть CelestialData в сигнатуру use. */
	private static final class CelestialDataKnown {
		static boolean known(ServerPlayer p, String id) {
			return dev.celestial.data.CelestialData.get(p).knowsLore(id);
		}
	}
}
