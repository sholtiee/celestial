package dev.celestial.item;

import dev.celestial.entity.LightSpear;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** Копьё Света: бросок по ПКМ, копьё возвращается само. */
public class LightSpearItem extends Item {
	public LightSpearItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.TRIDENT_THROW.value(), SoundSource.PLAYERS, 1.0F, 1.3F);
		if (level instanceof ServerLevel serverLevel) {
			stack.hurtAndBreak(1, player, hand.asEquipmentSlot());
			if (!stack.isEmpty()) {
				Projectile.spawnProjectileFromRotation(LightSpear::new, serverLevel, stack.copyWithCount(1), player, 0.0F, 2.5F, 0.5F);
			}
		}
		player.getCooldowns().addCooldown(stack, 30);
		if (!player.getAbilities().instabuild) {
			stack.shrink(1);
		}
		return InteractionResult.SUCCESS;
	}
}
