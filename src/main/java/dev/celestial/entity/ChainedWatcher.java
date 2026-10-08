package dev.celestial.entity;

import dev.celestial.data.CelestialData;
import dev.celestial.lore.Lore;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.server.level.ServerLevel;

/**
 * Прикованный Страж Темницы (Книга Еноха): не враг, а узник. Беседа (ПКМ) — три короткие реплики по кругу о том, как Стражи спустились и что за это было; первая открывает
 * лист Летописи «Наблюдатели» (и слово «Страж» в Глоссарии). Неуязвим, не двигается.
 */
public class ChainedWatcher extends PathfinderMob {
	private static final int LINES = 3;
	private int next;

	public ChainedWatcher(EntityType<? extends ChainedWatcher> type, Level level) {
		super(type, level);
		setPersistenceRequired();
	}

	public static AttributeSupplier.Builder createAttributes() {
		return PathfinderMob.createMobAttributes().add(Attributes.MAX_HEALTH, 40.0).add(Attributes.MOVEMENT_SPEED, 0.0);
	}

	@Override
	protected void registerGoals() {
		goalSelector.addGoal(1, new LookAtPlayerGoal(this, Player.class, 8.0F));
		goalSelector.addGoal(2, new RandomLookAroundGoal(this));
	}

	@Override
	protected InteractionResult mobInteract(Player player, InteractionHand hand) {
		if (player instanceof ServerPlayer sp && hand == InteractionHand.MAIN_HAND) {
			if (!CelestialData.get(sp).knowsLore("watchers")) {
				Lore.unlock(sp, "watchers");
			}
			sp.sendSystemMessage(Component.translatable("entity.celestial.chained_watcher").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(": ").withStyle(ChatFormatting.DARK_GRAY))
				.append(Component.translatable("entity.celestial.chained_watcher.line" + (next++ % LINES + 1)).withStyle(ChatFormatting.GRAY)));
			playSound(SoundEvents.CHAIN_BREAK, 0.6F, 0.5F);
			if (level() instanceof ServerLevel level) {
				level.sendParticles(ParticleTypes.SOUL, getX(), getY(1.0), getZ(), 6, 0.3, 0.5, 0.3, 0.02);
			}
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		return source.is(net.minecraft.tags.DamageTypeTags.BYPASSES_INVULNERABILITY) && super.hurtServer(level, source, amount);
	}

	@Override
	public boolean isPushable() {
		return false;
	}

	@Override
	public boolean removeWhenFarAway(double distSqr) {
		return false;
	}
}
