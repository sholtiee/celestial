package dev.celestial.item;

import dev.celestial.entity.SlingStone;
import dev.celestial.registry.ModItems;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** Праща: ПКМ метает камень из пращи (расходует «камень для пращи»), перезарядка 0,75 с. Против крупных целей урон втрое больше. */
public class SlingItem extends Item {
	public SlingItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack sling = player.getItemInHand(hand);
		ItemStack ammo = findAmmo(player);
		if (ammo.isEmpty() && !player.isCreative()) {
			return InteractionResult.FAIL;
		}
		if (!level.isClientSide()) {
			SlingStone stone = new SlingStone(level, player);
			stone.shootFromRotation(player, player.getXRot(), player.getYRot(), 0.0F, 1.7F, 1.0F);
			level.addFreshEntity(stone);
			level.playSound(null, player.blockPosition(), SoundEvents.SNOWBALL_THROW, SoundSource.PLAYERS, 0.8F, 0.6F + level.getRandom().nextFloat() * 0.2F);
			if (!player.isCreative()) {
				ammo.shrink(1);
				sling.hurtAndBreak(1, player, hand == InteractionHand.MAIN_HAND ? EquipmentSlot.MAINHAND : EquipmentSlot.OFFHAND);
			}
		}
		player.getCooldowns().addCooldown(sling, 15);
		return InteractionResult.SUCCESS;
	}

	private static ItemStack findAmmo(Player player) {
		for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
			ItemStack s = player.getInventory().getItem(i);
			if (s.is(ModItems.SLING_STONE)) {
				return s;
			}
		}
		return ItemStack.EMPTY;
	}
}
