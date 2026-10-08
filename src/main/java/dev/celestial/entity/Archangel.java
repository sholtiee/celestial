package dev.celestial.entity;

import dev.celestial.data.CelestialData;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
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
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * Архангел (LORE §4): Гавриил — вестник (труба), Уриил — свет (пламя), Михаил — сила (меч), Рафаил — исцеление (посох с рыбой).
 * Один тип сущности, четыре облика (Variant). Неуязвим, парит на месте; ПКМ — короткая беседа, зависящая от акта (реплики
 * `entity.celestial.archangel.<имя>.act<0..4>`). Первая беседа с каждым даёт Благодать +1 и запись в Кодекс.
 */
public class Archangel extends PathfinderMob {
	public static final String[] NAMES = {"gabriel", "uriel", "michael", "raphael"};
	private static final EntityDataAccessor<Integer> VARIANT = SynchedEntityData.defineId(Archangel.class, EntityDataSerializers.INT);

	public Archangel(EntityType<? extends Archangel> type, Level level) {
		super(type, level);
		setNoGravity(true);
		setPersistenceRequired();
	}

	public static AttributeSupplier.Builder createAttributes() {
		return PathfinderMob.createMobAttributes().add(Attributes.MAX_HEALTH, 60.0).add(Attributes.MOVEMENT_SPEED, 0.0);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(VARIANT, -1);
	}

	/** 0..3; пока не задан (яйцо призыва) — выбирается случайно и запоминается. */
	public int variant() {
		int v = entityData.get(VARIANT);
		if (v < 0 && !level().isClientSide()) {
			v = random.nextInt(NAMES.length);
			entityData.set(VARIANT, v);
		}
		return Math.max(0, v);
	}

	public void setVariant(int v) {
		entityData.set(VARIANT, Math.floorMod(v, NAMES.length));
	}

	public String archangelName() {
		return NAMES[variant()];
	}

	@Override
	protected Component getTypeName() {
		return Component.translatable("entity.celestial.archangel." + archangelName());
	}

	@Override
	protected void registerGoals() {
		goalSelector.addGoal(1, new LookAtPlayerGoal(this, Player.class, 12.0F));
		goalSelector.addGoal(2, new RandomLookAroundGoal(this));
	}

	@Override
	public void aiStep() {
		super.aiStep();
		setDeltaMovement(0, Math.sin(tickCount * 0.07 + variant()) * 0.012, 0);
		if (level().isClientSide() && random.nextInt(5) == 0) {
			level().addParticle(ParticleTypes.END_ROD, getRandomX(0.8), getRandomY(), getRandomZ(0.8), 0, 0.01, 0);
		}
	}

	@Override
	protected InteractionResult mobInteract(Player player, InteractionHand hand) {
		if (player instanceof ServerPlayer sp && hand == InteractionHand.MAIN_HAND) {
			String name = archangelName();
			var data = CelestialData.get(sp);
			if (!data.knows("archangel:" + name)) {
				CelestialData.update(sp, d -> d.withGrace(d.grace() + 1).withCodex("archangel:" + name).withCodex("mob:archangel"));
				((ServerLevel) level()).sendParticles(ParticleTypes.END_ROD, sp.getX(), sp.getY() + 1, sp.getZ(), 20, 0.4, 0.8, 0.4, 0.05);
			}
			int act = Math.min(4, CelestialData.world(sp.level().getServer()).act());
			sp.sendSystemMessage(Component.translatable("entity.celestial.archangel." + name).withStyle(ChatFormatting.GOLD)
				.append(Component.literal(": ").withStyle(ChatFormatting.DARK_GRAY))
				.append(Component.translatable("entity.celestial.archangel." + name + ".act" + act).withStyle(ChatFormatting.WHITE)));
			playSound(SoundEvents.AMETHYST_BLOCK_CHIME, 1.0F, 1.2F + 0.1F * variant());
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

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putInt("Variant", variant());
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		entityData.set(VARIANT, input.getIntOr("Variant", -1));
	}
}
