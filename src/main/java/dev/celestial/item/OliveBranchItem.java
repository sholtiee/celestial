package dev.celestial.item;

import dev.celestial.entity.Dove;
import dev.celestial.lore.Lore;
import dev.celestial.registry.ModEntities;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;

/** Масличная ветвь (Быт. 8:11): ПКМ — призвать голубя-проводника, который выведет к ближайшей постройке. Один голубь на игрока; ветвь служит шесть раз. */
public class OliveBranchItem extends Item {
	public OliveBranchItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (!(level instanceof ServerLevel server) || !(player instanceof ServerPlayer sp)) {
			return InteractionResult.SUCCESS;
		}
		for (Dove d : server.getEntitiesOfClass(Dove.class, new AABB(player.blockPosition()).inflate(64))) {
			if (player.getUUID().equals(d.owner())) {
				sp.sendOverlayMessage(Component.translatable("item.celestial.olive_branch.already"));
				return InteractionResult.FAIL;
			}
		}
		Dove dove = ModEntities.DOVE.create(server, EntitySpawnReason.TRIGGERED);
		if (dove == null) {
			return InteractionResult.FAIL;
		}
		dove.setOwner(player);
		dove.snapTo(player.getX(), player.getEyeY() + 1.0, player.getZ(), player.getYRot(), 0);
		server.addFreshEntity(dove);
		ItemStack stack = player.getItemInHand(hand);
		if (!player.isCreative()) {
			stack.hurtAndBreak(1, player, hand == InteractionHand.MAIN_HAND ? EquipmentSlot.MAINHAND : EquipmentSlot.OFFHAND);
		}
		Lore.unlock(sp, "dove");
		sp.sendOverlayMessage(Component.translatable("item.celestial.olive_branch.summoned"));
		return InteractionResult.SUCCESS;
	}
}
