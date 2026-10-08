package dev.celestial.entity;

import dev.celestial.registry.ModEntities;
import dev.celestial.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * Падший Серафим — босс Небесной Цитадели.
 * Фаза 1: ближний бой и рывки. Фаза 2: взлетает и обрушивает дождь световых копий.
 * Фаза 3: призывает падших стражей и бьёт молниями, копья падают чаще.
 */
public class FallenSeraph extends Monster {
	private final ServerBossEvent bossEvent = new ServerBossEvent(java.util.UUID.randomUUID(),
		Component.translatable("entity.celestial.fallen_seraph"), BossEvent.BossBarColor.YELLOW, BossEvent.BossBarOverlay.NOTCHED_10);
	private BlockPos home = BlockPos.ZERO;
	private int attackClock;
	private int phase = 1;
	/** Кристаллы света арены (появляются во 2-й фазе). Пока живы — лечат и ослабляют урон по Серафиму. */
	private final java.util.List<java.util.UUID> crystals = new java.util.ArrayList<>();
	private boolean crystalsSpawned;
	/** Отложенные атаки с предупреждением: что ударит, где и через сколько тиков. */
	private final java.util.List<Telegraph> telegraphs = new java.util.ArrayList<>();
	private int dashWindup;

	private enum Strike { SPEAR, SMITE, SHOCKWAVE }

	private static final class Telegraph {
		final Strike strike;
		final Vec3 at;
		int ticks;

		Telegraph(Strike strike, Vec3 at, int ticks) {
			this.strike = strike;
			this.at = at;
			this.ticks = ticks;
		}
	}

	public FallenSeraph(EntityType<? extends FallenSeraph> type, Level level) {
		super(type, level);
		bossEvent.setPlayBossMusic(true);
		this.xpReward = 600;
		this.setPersistenceRequired();
		this.setItemSlot(EquipmentSlot.CHEST, new ItemStack(ModItems.SERAPH_WINGS));
		this.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(ModItems.ETHERITE_SWORD));
		this.setDropChance(EquipmentSlot.CHEST, 0.0F);
		this.setDropChance(EquipmentSlot.MAINHAND, 0.0F);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
			.add(Attributes.MAX_HEALTH, 320.0)
			.add(Attributes.ARMOR, 8.0)
			.add(Attributes.ARMOR_TOUGHNESS, 2.0)
			.add(Attributes.ATTACK_DAMAGE, 12.0)
			.add(Attributes.MOVEMENT_SPEED, 0.32)
			.add(Attributes.FOLLOW_RANGE, 48.0)
			.add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
			.add(Attributes.SAFE_FALL_DISTANCE, 256.0);
	}

	public void setHome(BlockPos home) {
		this.home = home;
	}

	@Override
	protected void registerGoals() {
		this.goalSelector.addGoal(0, new FloatGoal(this));
		this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.2, true) {
			@Override
			public boolean canUse() {
				return phase == 1 && super.canUse();
			}

			@Override
			public boolean canContinueToUse() {
				return phase == 1 && super.canContinueToUse();
			}
		});
		this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 24.0F));
		this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
		this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, false));
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		bossEvent.setProgress(getHealth() / getMaxHealth());
		int newPhase = getHealth() > getMaxHealth() * 0.66F ? 1 : getHealth() > getMaxHealth() * 0.33F ? 2 : 3;
		if (newPhase != phase) {
			phase = newPhase;
			onPhaseChange(level);
		}
		setNoGravity(phase > 1);
		LivingEntity target = getTarget();
		attackClock++;
		tickTelegraphs(level);
		tickCrystals(level);
		if (target == null) {
			return;
		}
		if (phase == 1) {
			if (dashWindup > 0 && --dashWindup == 0) {
				dash(target);
			} else if (attackClock % 100 == 0 && onGround()) {
				// замах перед рывком: Серафим замирает и вспыхивает
				dashWindup = 15;
				setDeltaMovement(Vec3.ZERO);
				playSound(SoundEvents.WARDEN_SONIC_CHARGE, 1.5F, 1.4F);
				level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY(0.6), getZ(), 30, 0.5, 0.8, 0.5, 0.1);
			}
		} else {
			hover(target);
			int spearEvery = phase == 2 ? 50 : 35;
			if (attackClock % spearEvery == 0) {
				spearRain(level, target, phase == 2 ? 5 : 8);
			}
			if (phase == 3 && attackClock % 220 == 0) {
				summonGuardians(level);
			}
			if (phase == 3 && attackClock % 90 == 45) {
				telegraphs.add(new Telegraph(Strike.SMITE, Vec3.atBottomCenterOf(target.blockPosition()), 25));
			}
			if (phase == 3 && attackClock % 160 == 80) {
				// ударная волна света от земли под Серафимом: спасает только прыжок
				Vec3 ground = Vec3.atBottomCenterOf(home.equals(BlockPos.ZERO) ? target.blockPosition() : home);
				telegraphs.add(new Telegraph(Strike.SHOCKWAVE, ground, 30));
				for (ServerPlayer p : bossEvent.getPlayers()) {
					p.sendOverlayMessage(Component.translatable("boss.celestial.fallen_seraph.shockwave"));
				}
				playSound(SoundEvents.BEACON_POWER_SELECT, 3.0F, 0.5F);
			}
		}
	}

	/** Предупреждения: круг искр на земле, затем удар в это место (а не в игрока — можно увернуться). */
	private void tickTelegraphs(ServerLevel level) {
		var it = telegraphs.iterator();
		while (it.hasNext()) {
			Telegraph t = it.next();
			t.ticks--;
			if (t.strike == Strike.SHOCKWAVE) {
				double r = 7.0 * (1.0 - t.ticks / 30.0);
				for (int i = 0; i < 24; i++) {
					double a = i * Math.PI / 12;
					level.sendParticles(ParticleTypes.END_ROD, t.at.x + Math.cos(a) * r, t.at.y + 0.2, t.at.z + Math.sin(a) * r, 1, 0, 0, 0, 0);
				}
			} else if (t.ticks % 3 == 0) {
				for (int i = 0; i < 10; i++) {
					double a = i * Math.PI / 5 + t.ticks * 0.2;
					level.sendParticles(t.strike == Strike.SMITE ? ParticleTypes.ELECTRIC_SPARK : ParticleTypes.WAX_OFF,
						t.at.x + Math.cos(a) * 1.3, t.at.y + 0.15, t.at.z + Math.sin(a) * 1.3, 1, 0, 0, 0, 0);
				}
			}
			if (t.ticks > 0) {
				continue;
			}
			it.remove();
			switch (t.strike) {
				case SPEAR -> level.addFreshEntity(LightSpear.hostile(level, this, t.at.x, t.at.y + 14 + random.nextInt(4), t.at.z));
				case SMITE -> {
					LightningBolt bolt = EntityTypes.LIGHTNING_BOLT.create(level, EntitySpawnReason.TRIGGERED);
					if (bolt != null) {
						bolt.snapTo(t.at);
						level.addFreshEntity(bolt);
					}
				}
				case SHOCKWAVE -> {
					level.playSound(null, BlockPos.containing(t.at), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.0F, 1.6F);
					for (ServerPlayer p : bossEvent.getPlayers()) {
						if (p.distanceToSqr(t.at) < 9 * 9 && p.onGround()) {
							p.hurtServer(level, damageSources().indirectMagic(this, this), 9.0F);
							p.setDeltaMovement(p.position().subtract(t.at).normalize().scale(1.2).add(0, 0.5, 0));
							p.needsSync = true;
						}
					}
				}
			}
		}
	}

	/** Во 2-й фазе на арене встают 4 кристалла; каждый лечит Серафима на 1 здоровья в секунду. */
	private void tickCrystals(ServerLevel level) {
		if (phase >= 2 && !crystalsSpawned) {
			crystalsSpawned = true;
			BlockPos center = home.equals(BlockPos.ZERO) ? blockPosition() : home;
			for (int i = 0; i < 4; i++) {
				double a = i * Math.PI / 2 + Math.PI / 4;
				SeraphCrystal crystal = ModEntities.SERAPH_CRYSTAL.create(level, EntitySpawnReason.MOB_SUMMONED);
				if (crystal != null) {
					crystal.snapTo(center.getX() + 0.5 + Math.cos(a) * 9, center.getY() + 4, center.getZ() + 0.5 + Math.sin(a) * 9, 0, 0);
					level.addFreshEntity(crystal);
					crystals.add(crystal.getUUID());
					level.sendParticles(ParticleTypes.END_ROD, crystal.getX(), crystal.getY(), crystal.getZ(), 40, 0.5, 1, 0.5, 0.2);
				}
			}
			for (ServerPlayer p : bossEvent.getPlayers()) {
				p.sendSystemMessage(Component.translatable("boss.celestial.fallen_seraph.crystals"));
			}
		}
		if (crystals.isEmpty() || tickCount % 20 != 0) {
			return;
		}
		crystals.removeIf(id -> !(level.getEntity(id) instanceof SeraphCrystal c) || c.isRemoved());
		for (java.util.UUID id : crystals) {
			if (level.getEntity(id) instanceof SeraphCrystal crystal) {
				crystal.setBeamTarget(blockPosition().above(2));
				if (getHealth() < getMaxHealth()) {
					heal(1.0F);
				}
			}
		}
		if (crystals.isEmpty()) {
			for (ServerPlayer p : bossEvent.getPlayers()) {
				p.sendSystemMessage(Component.translatable("boss.celestial.fallen_seraph.crystals_gone"));
			}
		}
	}

	public boolean shieldedByCrystals() {
		return !crystals.isEmpty();
	}

	private void onPhaseChange(ServerLevel level) {
		playSound(dev.celestial.registry.ModSounds.SERAPH_ROAR, 3.0F, 1.0F);
		level.sendParticles(ParticleTypes.END_ROD, getX(), getY(1.0), getZ(), 80, 1.0, 1.5, 1.0, 0.3);
		Component line = Component.translatable("boss.celestial.fallen_seraph.phase" + phase);
		for (ServerPlayer p : bossEvent.getPlayers()) {
			p.sendSystemMessage(line);
		}
		applyPhaseLook();
		dev.celestial.boss.BossIntro.phase(bossEvent.getPlayers(), "fallen_seraph", phase,
			phase == 3 ? net.minecraft.ChatFormatting.RED : net.minecraft.ChatFormatting.GOLD);
		if (home.equals(BlockPos.ZERO)) {
			home = blockPosition();
		}
	}

	/** Вид полосы по фазе: золотая → белая (взмыл в небо) → красная и тёмный экран (ярость). */
	private void applyPhaseLook() {
		bossEvent.setColor(phase == 1 ? BossEvent.BossBarColor.YELLOW : phase == 2 ? BossEvent.BossBarColor.WHITE : BossEvent.BossBarColor.RED);
		bossEvent.setDarkenScreen(phase == 3);
	}

	/** Рывок к цели. */
	private void dash(LivingEntity target) {
		Vec3 dir = target.position().subtract(position()).normalize();
		setDeltaMovement(dir.x * 1.6, 0.35, dir.z * 1.6);
		playSound(SoundEvents.ENDER_DRAGON_FLAP, 1.5F, 0.8F);
	}

	/** Кружит над ареной на высоте 9 блоков, не улетая далеко от центра. */
	private void hover(LivingEntity target) {
		double angle = attackClock * (phase == 2 ? 0.02 : 0.035);
		double radius = phase == 2 ? 9.0 : 6.0;
		Vec3 center = Vec3.atBottomCenterOf(home.equals(BlockPos.ZERO) ? target.blockPosition() : home);
		Vec3 wanted = new Vec3(center.x + Math.cos(angle) * radius, center.y + 9.0 + Math.sin(attackClock * 0.05), center.z + Math.sin(angle) * radius);
		Vec3 delta = wanted.subtract(position());
		setDeltaMovement(getDeltaMovement().scale(0.8).add(delta.normalize().scale(Math.min(0.12, delta.length() * 0.05))));
		getLookControl().setLookAt(target, 30.0F, 30.0F);
		setYRot((float) (Mth.atan2(target.getZ() - getZ(), target.getX() - getX()) * Mth.RAD_TO_DEG) - 90.0F);
		yBodyRot = getYRot();
	}

	/** Световые копья: сначала на земле вспыхивают метки, через секунду в них бьют копья с неба. */
	private void spearRain(ServerLevel level, LivingEntity target, int count) {
		Vec3 lead = target.position().add(target.getDeltaMovement().scale(12));
		for (int i = 0; i < count; i++) {
			double x = lead.x + (random.nextDouble() - 0.5) * 7;
			double z = lead.z + (random.nextDouble() - 0.5) * 7;
			telegraphs.add(new Telegraph(Strike.SPEAR, new Vec3(x, target.getY(), z), 20));
		}
		playSound(SoundEvents.AMETHYST_CLUSTER_BREAK, 2.0F, 0.6F);
	}

	private void summonGuardians(ServerLevel level) {
		for (int i = 0; i < 2; i++) {
			FallenGuardian guardian = ModEntities.FALLEN_GUARDIAN.create(level, EntitySpawnReason.MOB_SUMMONED);
			if (guardian != null) {
				BlockPos at = (home.equals(BlockPos.ZERO) ? blockPosition() : home).offset(random.nextInt(9) - 4, 1, random.nextInt(9) - 4);
				guardian.snapTo(at, random.nextFloat() * 360F, 0);
				guardian.finalizeSpawn(level, level.getCurrentDifficultyAt(at), EntitySpawnReason.MOB_SUMMONED, null);
				guardian.setTarget(getTarget());
				level.addFreshEntity(guardian);
				level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, at.getX() + 0.5, at.getY() + 0.5, at.getZ() + 0.5, 20, 0.3, 0.6, 0.3, 0.02);
			}
		}
	}

	@Override
	public void thunderHit(ServerLevel level, LightningBolt bolt) {
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (shieldedByCrystals() && !source.is(net.minecraft.tags.DamageTypeTags.BYPASSES_INVULNERABILITY)) {
			amount *= 0.5F;
			level.sendParticles(ParticleTypes.WAX_ON, getX(), getY(0.6), getZ(), 6, 0.5, 0.8, 0.5, 0.05);
		}
		if (source.getDirectEntity() instanceof LightSpear spear && spear.isBossSpear() || source.is(net.minecraft.tags.DamageTypeTags.IS_FALL)) {
			return false;
		}
		return super.hurtServer(level, source, amount);
	}

	@Override
	public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
		return false;
	}

	@Override
	protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {
	}

	@Override
	public boolean canUsePortal(boolean ignorePassenger) {
		return false;
	}

	@Override
	public boolean removeWhenFarAway(double distSqr) {
		return false;
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
	public void die(DamageSource source) {
		super.die(source);
		if (level() instanceof ServerLevel level) {
			level.sendParticles(ParticleTypes.END_ROD, getX(), getY(1.0), getZ(), 200, 1.5, 2.0, 1.5, 0.4);
			level.playSound(null, blockPosition(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.HOSTILE, 2.0F, 1.0F);
			dev.celestial.story.StoryEvents.onSeraphDefeated(level, this, source);
			for (java.util.UUID id : crystals) {
				if (level.getEntity(id) instanceof SeraphCrystal crystal) {
					crystal.discard();
				}
			}
		}
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.store("Home", BlockPos.CODEC, home);
		output.putBoolean("CrystalsSpawned", crystalsSpawned);
		output.putInt("Phase", phase);  // без фазы после перезахода реплики и эффекты фаз повторялись
		output.store("Crystals", net.minecraft.core.UUIDUtil.CODEC.listOf(), crystals);
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		home = input.read("Home", BlockPos.CODEC).orElse(BlockPos.ZERO);
		crystalsSpawned = input.getBooleanOr("CrystalsSpawned", false);
		phase = input.getIntOr("Phase", 1);
		applyPhaseLook();
		crystals.clear();
		crystals.addAll(input.read("Crystals", net.minecraft.core.UUIDUtil.CODEC.listOf()).orElse(java.util.List.of()));
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return SoundEvents.EVOKER_AMBIENT;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.IRON_GOLEM_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.WITHER_DEATH;
	}

	@Override
	public float getVoicePitch() {
		return 0.7F;
	}
}
