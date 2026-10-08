package dev.celestial.entity;

import dev.celestial.data.CelestialData;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
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

/**
 * Иния — предводительница вмёрзших ангелов, освобождённая после победы над Морозным Архонтом. Неуязвима, парит на месте.
 * Разговор (ПКМ) рассказывает о Безликом и ведёт к следующему акту; при первой беседе — благословение (Благодать +2).
 */
public class Inia extends PathfinderMob {
	private static final int LINES = 4;

	public Inia(EntityType<? extends Inia> type, Level level) {
		super(type, level);
		setNoGravity(true);
		setPersistenceRequired();
	}

	public static AttributeSupplier.Builder createAttributes() {
		return PathfinderMob.createMobAttributes().add(Attributes.MAX_HEALTH, 40.0).add(Attributes.MOVEMENT_SPEED, 0.0);
	}

	@Override
	protected void registerGoals() {
		goalSelector.addGoal(1, new LookAtPlayerGoal(this, Player.class, 12.0F));
		goalSelector.addGoal(2, new RandomLookAroundGoal(this));
	}

	@Override
	public void aiStep() {
		super.aiStep();
		setDeltaMovement(0, Math.sin(tickCount * 0.08) * 0.01, 0);
		if (level().isClientSide() && random.nextInt(4) == 0) {
			level().addParticle(ParticleTypes.END_ROD, getRandomX(0.6), getRandomY(), getRandomZ(0.6), 0, 0.01, 0);
		}
	}

	@Override
	protected InteractionResult mobInteract(Player player, InteractionHand hand) {
		if (player instanceof ServerPlayer sp && hand == InteractionHand.MAIN_HAND) {
			var data = CelestialData.get(sp);
			int line = (int) (level().getGameTime() / 60 % LINES) + 1;
			if (!data.knows("inia_blessing")) {
				line = 1;
				CelestialData.update(sp, d -> d.withGrace(d.grace() + 2).withCodex("inia_blessing"));
				sp.sendSystemMessage(Component.translatable("entity.celestial.inia.blessing").withStyle(ChatFormatting.AQUA));
				((ServerLevel) level()).sendParticles(ParticleTypes.END_ROD, sp.getX(), sp.getY() + 1, sp.getZ(), 30, 0.4, 0.8, 0.4, 0.05);
			}
			sp.sendSystemMessage(Component.translatable("entity.celestial.inia.line" + line).withStyle(ChatFormatting.WHITE));
			playSound(SoundEvents.AMETHYST_BLOCK_CHIME, 1.0F, 1.4F);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		return source.is(net.minecraft.tags.DamageTypeTags.BYPASSES_INVULNERABILITY) && super.hurtServer(level, source, amount);  // только /kill
	}

	@Override
	public boolean causeFallDamage(double fallDistance, float multiplier, DamageSource source) {
		return false;
	}

	@Override
	public boolean removeWhenFarAway(double distSqr) {
		return false;
	}

	@Override
	public boolean isPushable() {
		return false;
	}
}
