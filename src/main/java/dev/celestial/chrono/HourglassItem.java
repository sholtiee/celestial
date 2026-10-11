package dev.celestial.chrono;

import net.minecraft.core.particles.ParticleTypes;
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
 * Песочные часы (реликвия Акта IV): ПКМ — на {@link #TICKS} тиков останавливает время в сфере R={@link #RADIUS}:
 * мобы и снаряды замирают (свои снаряды и сам владелец — нет, другие игроки — нет). Боссы лишь замедляются (тег time_immune).
 */
public class HourglassItem extends Item {
	public static final double RADIUS = 10.0;
	public static final int TICKS = 100;
	public static final int COOLDOWN = 600;

	public HourglassItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BELL_RESONATE, SoundSource.PLAYERS, 1.0F, 0.6F);
		if (level instanceof ServerLevel server) {
			TimeFlow.stop(server, player.position(), RADIUS, TICKS, false, player);
			for (int i = 0; i < 48; i++) {
				double a = i * Math.PI * 2 / 48;
				server.sendParticles(ParticleTypes.END_ROD, player.getX() + Math.cos(a) * RADIUS, player.getY() + 0.3,
					player.getZ() + Math.sin(a) * RADIUS, 1, 0, 0.2, 0, 0.0);
			}
			stack.hurtAndBreak(1, player, hand.asEquipmentSlot());
		}
		player.getCooldowns().addCooldown(stack, COOLDOWN);
		return InteractionResult.SUCCESS;
	}
}
