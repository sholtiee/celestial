package dev.celestial.entity;

import dev.celestial.registry.ModEntities;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.BossEvent;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.Level;

/** Грозовой элементаль: мини-босс Грозового пика. Как грозовой дух, но огромный, с полосой здоровья и свитой. */
public class StormElemental extends StormSpirit {
	private final ServerBossEvent bossEvent = new ServerBossEvent(java.util.UUID.randomUUID(),
		Component.translatable("entity.celestial.storm_elemental"), BossEvent.BossBarColor.BLUE, BossEvent.BossBarOverlay.PROGRESS);
	private int summonClock;

	public StormElemental(EntityType<? extends StormElemental> type, Level level) {
		super(type, level);
		this.xpReward = 120;
		this.setPersistenceRequired();
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
			.add(Attributes.MAX_HEALTH, 140.0).add(Attributes.ATTACK_DAMAGE, 9.0).add(Attributes.ARMOR, 6.0)
			.add(Attributes.MOVEMENT_SPEED, 0.27).add(Attributes.FOLLOW_RANGE, 48.0).add(Attributes.KNOCKBACK_RESISTANCE, 1.0);
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		bossEvent.setProgress(getHealth() / getMaxHealth());
		if (getTarget() != null && ++summonClock % 260 == 0) {
			for (int i = 0; i < 2; i++) {
				StormSpirit spirit = ModEntities.STORM_SPIRIT.create(level, EntitySpawnReason.MOB_SUMMONED);
				if (spirit != null) {
					spirit.snapTo(getX() + random.nextInt(7) - 3, getY() + 1, getZ() + random.nextInt(7) - 3, 0, 0);
					spirit.setTarget(getTarget());
					level.addFreshEntity(spirit);
				}
			}
		}
	}

	@Override
	public void startSeenByPlayer(ServerPlayer player) {
		super.startSeenByPlayer(player);
		bossEvent.addPlayer(player);
	}

	@Override
	public void stopSeenByPlayer(ServerPlayer player) {
		super.stopSeenByPlayer(player);
		bossEvent.removePlayer(player);
	}

	@Override
	public boolean removeWhenFarAway(double distSqr) {
		return false;
	}
}
