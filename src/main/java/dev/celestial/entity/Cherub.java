package dev.celestial.entity;

import java.util.Optional;
import java.util.UUID;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.animal.allay.Allay;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

/**
 * Херувим: как Аллай (дай предмет — будет собирать такие же и приносить),
 * но ещё и раз в полминуты подлечивает «своего» игрока, если тот ранен.
 */
public class Cherub extends Allay {
	private int healCooldown;

	public Cherub(EntityType<? extends Cherub> type, Level level) {
		super(type, level);
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (healCooldown > 0) {
			healCooldown--;
			return;
		}
		Optional<UUID> liked = getBrain().getMemory(MemoryModuleType.LIKED_PLAYER);
		if (liked.isEmpty()) {
			return;
		}
		Player player = level.getPlayerByUUID(liked.get());
		if (player != null && player.isAlive() && player.getHealth() < player.getMaxHealth() && distanceToSqr(player) < 64) {
			player.heal(4.0F);
			level.sendParticles(net.minecraft.core.particles.ParticleTypes.HEART, player.getX(), player.getY(1.0), player.getZ(), 3, 0.3, 0.2, 0.3, 0);
			playSound(net.minecraft.sounds.SoundEvents.ALLAY_ITEM_GIVEN, 1.0F, 1.4F);
			healCooldown = 600;
		}
	}
}
