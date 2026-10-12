package dev.celestial.chrono;

import dev.celestial.registry.ModParticles;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * Шестерня Вечности — реликвия Акта IV, сердце часов Хронограда. ПКМ: на {@link #TICKS} тиков вокруг тебя (8 блоков)
 * время тянется для всех, кроме игроков, а ты сам ускорен. Откат {@link #COOLDOWN}. Понадобится в финале.
 */
public class GearOfEternityItem extends Item {
	public static final int TICKS = 160;
	public static final int COOLDOWN = 800;

	public GearOfEternityItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BELL_RESONATE, SoundSource.PLAYERS, 1.0F, 1.4F);
		if (level instanceof ServerLevel server) {
			TimeFlow.aura(server, player, TICKS);
			for (int i = 0; i < 40; i++) {
				double a = i * Math.PI * 2 / 40;
				server.sendParticles(ModParticles.CHRONO_HASTE, player.getX() + Math.cos(a) * TimeFlow.AURA_RADIUS, player.getY() + 0.5,
					player.getZ() + Math.sin(a) * TimeFlow.AURA_RADIUS, 1, 0, 0.1, 0, 0.0);
			}
		}
		player.getCooldowns().addCooldown(stack, ChronoGear.cooldown(player, COOLDOWN));
		return InteractionResult.SUCCESS;
	}
}
