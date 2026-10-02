package dev.celestial.block.machine;

import dev.celestial.registry.ModBlocks;
import dev.celestial.registry.ModItems;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Небесная кузня (мультиблок): ядро, четыре блока светлого камня по сторонам и луч света в ядро.
 * ПКМ предметом: алмазное снаряжение → эфиритовое (2 эфирита + звёздный кварц из инвентаря),
 * эфиритовое — полный ремонт за звёздный кварц. Зачарования сохраняются.
 */
public class CelestialForgeBlock extends Block implements BeamPowered {
	private record Upgrade(Item from, Item to) {}

	private static List<Upgrade> upgrades() {
		return List.of(
			new Upgrade(Items.DIAMOND_SWORD, ModItems.ETHERITE_SWORD), new Upgrade(Items.DIAMOND_PICKAXE, ModItems.ETHERITE_PICKAXE),
			new Upgrade(Items.DIAMOND_AXE, ModItems.ETHERITE_AXE), new Upgrade(Items.DIAMOND_SHOVEL, ModItems.ETHERITE_SHOVEL),
			new Upgrade(Items.DIAMOND_HOE, ModItems.ETHERITE_HOE), new Upgrade(Items.DIAMOND_HELMET, ModItems.ETHERITE_HELMET),
			new Upgrade(Items.DIAMOND_CHESTPLATE, ModItems.ETHERITE_CHESTPLATE), new Upgrade(Items.DIAMOND_LEGGINGS, ModItems.ETHERITE_LEGGINGS),
			new Upgrade(Items.DIAMOND_BOOTS, ModItems.ETHERITE_BOOTS));
	}

	public CelestialForgeBlock(Properties properties) {
		super(properties);
	}

	public static boolean isComplete(Level level, BlockPos pos) {
		for (Direction d : Direction.Plane.HORIZONTAL) {
			if (!level.getBlockState(pos.relative(d)).is(ModBlocks.RADIANT_STONE)) {
				return false;
			}
		}
		return true;
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand, BlockHitResult hit) {
		if (!(level instanceof ServerLevel server)) {
			return InteractionResult.SUCCESS;
		}
		if (!isComplete(level, pos)) {
			player.sendOverlayMessage(Component.translatable("machine.celestial.forge.incomplete"));
			return InteractionResult.FAIL;
		}
		if (!BeamPowered.isPowered(level, pos)) {
			player.sendOverlayMessage(Component.translatable("machine.celestial.forge.no_light"));
			return InteractionResult.FAIL;
		}
		for (Upgrade up : upgrades()) {
			if (stack.is(up.from())) {
				if (!pay(player, ModItems.ETHERITE_INGOT, 2, ModItems.STARQUARTZ, 1)) {
					player.sendOverlayMessage(Component.translatable("machine.celestial.forge.cost_upgrade"));
					return InteractionResult.FAIL;
				}
				player.setItemInHand(hand, stack.transmuteCopy(up.to(), 1));
				done(server, pos, player);
				return InteractionResult.SUCCESS;
			}
		}
		if (stack.isDamageableItem() && stack.isDamaged() && net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(stack.getItem()).getNamespace().equals("celestial")) {
			if (!pay(player, ModItems.STARQUARTZ, 1, null, 0)) {
				player.sendOverlayMessage(Component.translatable("machine.celestial.forge.cost_repair"));
				return InteractionResult.FAIL;
			}
			stack.setDamageValue(0);
			done(server, pos, player);
			return InteractionResult.SUCCESS;
		}
		player.sendOverlayMessage(Component.translatable("machine.celestial.forge.hint"));
		return InteractionResult.PASS;
	}

	private static boolean pay(Player player, Item a, int na, Item b, int nb) {
		if (player.getAbilities().instabuild) {
			return true;
		}
		var inv = player.getInventory();
		if (inv.countItem(a) < na || (b != null && inv.countItem(b) < nb)) {
			return false;
		}
		take(player, a, na);
		if (b != null) {
			take(player, b, nb);
		}
		return true;
	}

	private static void take(Player player, Item item, int count) {
		var inv = player.getInventory();
		for (int i = 0; i < inv.getContainerSize() && count > 0; i++) {
			ItemStack s = inv.getItem(i);
			if (s.is(item)) {
				int n = Math.min(count, s.getCount());
				s.shrink(n);
				count -= n;
			}
		}
	}

	private static void done(ServerLevel level, BlockPos pos, Player player) {
		level.playSound(null, pos, SoundEvents.SMITHING_TABLE_USE, SoundSource.BLOCKS, 1.0F, 1.0F);
		level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 1.0F, 1.4F);
		level.sendParticles(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5, 30, 0.3, 0.3, 0.3, 0.1);
		player.sendOverlayMessage(Component.translatable("machine.celestial.forge.done"));
	}
}
