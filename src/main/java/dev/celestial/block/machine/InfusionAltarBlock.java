package dev.celestial.block.machine;

import dev.celestial.Celestial;
import dev.celestial.item.RuneItem;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Алтарь наделения: держишь руну в другой руке, ПКМ по алтарю снаряжением — руна вплетается в него
 * небесным зачарованием (только через алтарь, на столе зачарований их нет). Нужен луч света и 3 уровня опыта.
 */
public class InfusionAltarBlock extends Block implements BeamPowered {
	private static final int XP_COST = 3;

	public InfusionAltarBlock(Properties properties) {
		super(properties);
	}

	@Override
	protected InteractionResult useItemOn(ItemStack gear, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand, BlockHitResult hit) {
		if (!(level instanceof ServerLevel server)) {
			return InteractionResult.SUCCESS;
		}
		InteractionHand other = hand == InteractionHand.MAIN_HAND ? InteractionHand.OFF_HAND : InteractionHand.MAIN_HAND;
		ItemStack rune = player.getItemInHand(other);
		if (!(rune.getItem() instanceof RuneItem runeItem)) {
			player.sendOverlayMessage(Component.translatable("machine.celestial.infusion.hint"));
			return InteractionResult.PASS;
		}
		if (!BeamPowered.isPowered(level, pos)) {
			player.sendOverlayMessage(Component.translatable("machine.celestial.forge.no_light"));
			return InteractionResult.FAIL;
		}
		if (player.experienceLevel < XP_COST && !player.getAbilities().instabuild) {
			player.sendOverlayMessage(Component.translatable("machine.celestial.infusion.xp"));
			return InteractionResult.FAIL;
		}
		var registry = server.registryAccess().lookupOrThrow(Registries.ENCHANTMENT);
		for (String id : runeItem.enchantments()) {
			Holder<Enchantment> ench = registry.getOrThrow(ResourceKey.create(Registries.ENCHANTMENT, Celestial.id(id)));
			if (!ench.value().canEnchant(gear)) {
				continue;
			}
			int current = EnchantmentHelper.getItemEnchantmentLevel(ench, gear);
			if (current >= ench.value().getMaxLevel()) {
				player.sendOverlayMessage(Component.translatable("machine.celestial.infusion.max"));
				return InteractionResult.FAIL;
			}
			gear.enchant(ench, current + 1);
			rune.consume(1, player);
			if (!player.getAbilities().instabuild) {
				player.giveExperienceLevels(-XP_COST);
			}
			server.playSound(null, pos, SoundEvents.ENCHANTMENT_TABLE_USE, SoundSource.BLOCKS, 1.0F, 1.3F);
			server.sendParticles(ParticleTypes.ENCHANT, pos.getX() + 0.5, pos.getY() + 1.5, pos.getZ() + 0.5, 60, 0.5, 0.5, 0.5, 0.6);
			player.sendOverlayMessage(Component.translatable("machine.celestial.infusion.done", ench.value().description()));
			return InteractionResult.SUCCESS;
		}
		player.sendOverlayMessage(Component.translatable("machine.celestial.infusion.unsuitable"));
		return InteractionResult.FAIL;
	}
}
