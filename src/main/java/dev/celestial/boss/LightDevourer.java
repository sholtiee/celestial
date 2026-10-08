package dev.celestial.boss;

import dev.celestial.data.CelestialData;
import dev.celestial.registry.ModEntities;
import dev.celestial.registry.ModSounds;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Пожиратель Света — страж Бездны, босс Акта II. Огромный «скат тьмы», который кружит под сводом Логова.
 * Пока на арене горит меньше двух жаровен, он поглощает почти весь урон; сам он охотится за огнём и гасит жаровни.
 * Фазы: 1 — пике на игроков; 2 — дыхание тьмы и призыв Светоедов; 3 — гасит всё и затягивает игроков в пасть.
 */
public class LightDevourer extends Monster {
	/** «Быстрее тьмы»: победа не дольше 7 минут от начала боя (жаровни зажигать тоже время). */
	private static final int SWIFT_TICKS = 7 * 60 * 20;
	/** Учёт боя для достижений «без урона» и «быстро». */
	private final BossRecord record = new BossRecord();
	private enum Mode { CIRCLE, SWOOP, EXTINGUISH, PULL }

	private static final EntityDataAccessor<Integer> LIT_BRAZIERS = SynchedEntityData.defineId(LightDevourer.class, EntityDataSerializers.INT);
	private final ServerBossEvent bossEvent = new ServerBossEvent(java.util.UUID.randomUUID(), Component.translatable("entity.celestial.light_devourer"),
		BossEvent.BossBarColor.PURPLE, BossEvent.BossBarOverlay.NOTCHED_10);
	private BlockPos home = BlockPos.ZERO;
	private final List<BlockPos> braziers = new ArrayList<>();
	private Mode mode = Mode.CIRCLE;
	private int modeTicks;
	private int clock;
	private int phase = 1;
	private @Nullable BlockPos brazierTarget;
	private @Nullable Vec3 swoopTarget;
	private int absorbMessageCooldown;

	public LightDevourer(EntityType<? extends LightDevourer> type, Level level) {
		super(type, level);
		this.xpReward = 200;
		setNoGravity(true);
		bossEvent.setPlayBossMusic(true);
		bossEvent.setDarkenScreen(true);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
			.add(Attributes.MAX_HEALTH, 420.0)
			.add(Attributes.ATTACK_DAMAGE, 12.0)
			.add(Attributes.ARMOR, 10.0)
			.add(Attributes.FOLLOW_RANGE, 64.0)
			.add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
			.add(Attributes.MOVEMENT_SPEED, 0.3);
	}

	public void setHome(BlockPos home) {
		this.home = home.immutable();
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(LIT_BRAZIERS, 0);
	}

	/** Для рендера: сколько жаровен горит (при ≥2 Пожиратель «проявлен» — светятся жилы). */
	public int litBraziers() {
		return entityData.get(LIT_BRAZIERS);
	}

	public boolean exposed() {
		return litBraziers() >= 2;
	}

	@Override
	protected void registerGoals() {
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		record.tick(level, bossEvent.getPlayers());
		clock++;
		modeTicks++;
		if (absorbMessageCooldown > 0) {
			absorbMessageCooldown--;
		}
		if (home.equals(BlockPos.ZERO)) {
			home = blockPosition().below(9);
		}
		if (braziers.isEmpty() || clock % 200 == 0) {
			scanBraziers(level);
		}
		int lit = (int) braziers.stream().filter(p -> isLit(level, p)).count();
		entityData.set(LIT_BRAZIERS, lit);
		bossEvent.setProgress(getHealth() / getMaxHealth());
		bossEvent.setColor(lit >= 2 ? BossEvent.BossBarColor.YELLOW : BossEvent.BossBarColor.PURPLE);

		int newPhase = getHealth() > getMaxHealth() * 0.6F ? 1 : getHealth() > getMaxHealth() * 0.3F ? 2 : 3;
		if (newPhase != phase) {
			phase = newPhase;
			onPhase(level);
		}
		LivingEntity target = findTarget(level);
		switch (mode) {
			case CIRCLE -> circle(target);
			case SWOOP -> swoop(level);
			case EXTINGUISH -> extinguish(level);
			case PULL -> pull(level);
		}
		if (mode == Mode.CIRCLE && target != null) {
			int extinguishEvery = phase == 1 ? 220 : phase == 2 ? 170 : 130;
			if (lit > 0 && clock % extinguishEvery == 0) {
				brazierTarget = braziers.stream().filter(p -> isLit(level, p)).skip(random.nextInt(lit)).findFirst().orElse(null);
				if (brazierTarget != null) {
					setMode(Mode.EXTINGUISH);
					for (ServerPlayer p : bossEvent.getPlayers()) {
						p.sendOverlayMessage(Component.translatable("boss.celestial.light_devourer.hunts_fire"));
					}
				}
			} else if (clock % 90 == 45) {
				swoopTarget = target.position().add(0, 1, 0);
				setMode(Mode.SWOOP);
				playSound(ModSounds.DEVOURER_ROAR, 2.0F, 1.3F);
			} else if (phase >= 2 && clock % 140 == 70) {
				breath(level, target);
			} else if (phase == 3 && clock % 260 == 130) {
				setMode(Mode.PULL);
			}
			if (phase >= 2 && clock % 300 == 0) {
				summon(level);
			}
		}
	}

	private void setMode(Mode m) {
		mode = m;
		modeTicks = 0;
	}

	private @Nullable LivingEntity findTarget(ServerLevel level) {
		LivingEntity target = getTarget();
		if (target == null || !target.isAlive() || distanceToSqr(target) > 64 * 64 || target instanceof Player p && (p.isCreative() || p.isSpectator())) {
			target = level.getNearestPlayer(getX(), getY(), getZ(), 48.0, p -> p instanceof Player pl && !pl.isCreative() && !pl.isSpectator());
			setTarget(target);
		}
		return target;
	}

	private void scanBraziers(ServerLevel level) {
		braziers.clear();
		for (BlockPos p : BlockPos.betweenClosed(home.offset(-20, -4, -20), home.offset(20, 8, 20))) {
			if (level.getBlockState(p).getBlock() instanceof BrazierBlock) {
				braziers.add(p.immutable());
			}
		}
	}

	private static boolean isLit(ServerLevel level, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		return state.getBlock() instanceof BrazierBlock && state.getValue(BrazierBlock.LIT);
	}

	/** Кружит под сводом над центром Логова. */
	private void circle(@Nullable LivingEntity target) {
		double angle = clock * (phase == 3 ? 0.035 : 0.025);
		Vec3 center = Vec3.atBottomCenterOf(home);
		Vec3 wanted = new Vec3(center.x + Math.cos(angle) * 11, center.y + 9 + Math.sin(clock * 0.05) * 1.5, center.z + Math.sin(angle) * 11);
		steer(wanted, 0.09);
		if (target != null) {
			faceTowards(target.position());
		}
	}

	private void steer(Vec3 wanted, double maxSpeed) {
		Vec3 delta = wanted.subtract(position());
		setDeltaMovement(getDeltaMovement().scale(0.8).add(delta.normalize().scale(Math.min(maxSpeed, delta.length() * 0.06))));
	}

	private void faceTowards(Vec3 point) {
		setYRot((float) (Mth.atan2(point.z - getZ(), point.x - getX()) * Mth.RAD_TO_DEG) - 90.0F);
		yBodyRot = getYRot();
		yHeadRot = getYRot();
	}

	/** Пике: несётся в точку, где был игрок, и бьёт всех, кого заденет. */
	private void swoop(ServerLevel level) {
		if (swoopTarget == null || modeTicks > 45) {
			setMode(Mode.CIRCLE);
			return;
		}
		Vec3 delta = swoopTarget.subtract(position());
		setDeltaMovement(delta.normalize().scale(Math.min(1.1, 0.4 + modeTicks * 0.05)));
		faceTowards(swoopTarget);
		for (ServerPlayer p : level.getEntitiesOfClass(ServerPlayer.class, getBoundingBox().inflate(1.0))) {
			if (p.hurtServer(level, damageSources().mobAttack(this), (float) getAttributeValue(Attributes.ATTACK_DAMAGE))) {
				p.setDeltaMovement(getDeltaMovement().scale(0.8).add(0, 0.5, 0));
				p.needsSync = true;
			}
		}
		if (delta.length() < 1.5) {
			setMode(Mode.CIRCLE);
		}
	}

	/** Летит к горящей жаровне и гасит её. */
	private void extinguish(ServerLevel level) {
		if (brazierTarget == null || !isLit(level, brazierTarget) || modeTicks > 160) {
			setMode(Mode.CIRCLE);
			return;
		}
		Vec3 over = Vec3.atCenterOf(brazierTarget).add(0, 2.5, 0);
		steer(over, 0.35);
		faceTowards(over);
		level.sendParticles(dev.celestial.registry.ModParticles.SHADOW, getX(), getY(0.5), getZ(), 3, 1.5, 0.3, 1.5, 0.01);
		if (position().distanceToSqr(over) < 6) {
			BrazierBlock.extinguish(level, brazierTarget, level.getBlockState(brazierTarget));
			playSound(ModSounds.DEVOURER_ROAR, 2.5F, 0.8F);
			setMode(Mode.CIRCLE);
		}
	}

	/** Дыхание тьмы: конус перед мордой — Тьма и прилив страха. */
	private void breath(ServerLevel level, LivingEntity target) {
		faceTowards(target.position());
		Vec3 look = target.position().subtract(position()).normalize();
		for (int i = 1; i <= 12; i++) {
			Vec3 p = position().add(look.scale(i));
			level.sendParticles(dev.celestial.registry.ModParticles.SHADOW, p.x, p.y + 1, p.z, 8, 0.4 + i * 0.12, 0.4, 0.4 + i * 0.12, 0.02);
		}
		for (ServerPlayer p : bossEvent.getPlayers()) {
			Vec3 to = p.position().subtract(position());
			if (to.length() < 14 && to.normalize().dot(look) > 0.75) {
				p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 120, 0));
				CelestialData.update(p, d -> d.withFear(d.fear() + 25));
				p.hurtServer(level, damageSources().magic(), 4.0F);
			}
		}
		playSound(SoundEvents.WARDEN_SONIC_BOOM, 2.0F, 0.6F);
	}

	/** 3-я фаза: зависает в центре и затягивает игроков в пасть. */
	private void pull(ServerLevel level) {
		steer(Vec3.atBottomCenterOf(home).add(0, 6, 0), 0.2);
		if (modeTicks % 2 == 0) {
			for (int i = 0; i < 20; i++) {
				double a = random.nextDouble() * Math.PI * 2;
				double r = 4 + random.nextDouble() * 10;
				level.sendParticles(dev.celestial.registry.ModParticles.RIFT, getX() + Math.cos(a) * r, getY() - 2 + random.nextDouble() * 4,
					getZ() + Math.sin(a) * r, 1, 0, 0, 0, 0.0);
			}
		}
		for (ServerPlayer p : bossEvent.getPlayers()) {
			Vec3 to = position().subtract(p.position());
			if (to.length() < 18) {
				p.setDeltaMovement(p.getDeltaMovement().add(to.normalize().scale(0.07)));
				p.needsSync = true;
				if (to.length() < 3.5 && modeTicks % 10 == 0) {
					p.hurtServer(level, damageSources().mobAttack(this), 4.0F);
				}
			}
		}
		if (modeTicks > 70) {
			setMode(Mode.CIRCLE);
		}
	}

	private void summon(ServerLevel level) {
		for (int i = 0; i < 3; i++) {
			Mob mob = (i < 2 ? ModEntities.LIGHT_EATER : ModEntities.SHADOW).create(level, EntitySpawnReason.MOB_SUMMONED);
			if (mob != null) {
				mob.addTag(dev.celestial.world.abyss.Darkness.NO_REPEL);
			}
			if (mob != null) {
				BlockPos at = home.offset(random.nextInt(13) - 6, 2, random.nextInt(13) - 6);
				mob.snapTo(at, random.nextFloat() * 360, 0);
				level.addFreshEntity(mob);
				level.sendParticles(dev.celestial.registry.ModParticles.SHADOW, at.getX() + 0.5, at.getY() + 0.5, at.getZ() + 0.5, 20, 0.3, 0.5, 0.3, 0.02);
			}
		}
	}

	private void onPhase(ServerLevel level) {
		playSound(ModSounds.DEVOURER_ROAR, 4.0F, 0.7F);
		for (ServerPlayer p : bossEvent.getPlayers()) {
			p.sendSystemMessage(Component.translatable("boss.celestial.light_devourer.phase" + phase));
		}
		BossIntro.phase(bossEvent.getPlayers(), "light_devourer", phase,
			phase == 3 ? net.minecraft.ChatFormatting.DARK_RED : net.minecraft.ChatFormatting.DARK_PURPLE);
		if (phase == 3) {
			for (BlockPos b : braziers) {
				if (isLit(level, b)) {
					BrazierBlock.extinguish(level, b, level.getBlockState(b));
				}
			}
		}
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (!exposed() && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
			amount *= 0.08F;
			level.sendParticles(dev.celestial.registry.ModParticles.SHADOW, getX(), getY(0.5), getZ(), 15, 1.2, 0.5, 1.2, 0.05);
			if (absorbMessageCooldown == 0 && source.getEntity() instanceof ServerPlayer player) {
				player.sendOverlayMessage(Component.translatable("boss.celestial.light_devourer.absorbs"));
				absorbMessageCooldown = 60;
			}
		}
		// до super: смертельный удар вызывает die() прямо внутри hurtServer, и последний ударивший должен уже быть записан
		record.dealt(source);
		return super.hurtServer(level, source, amount);
	}

	@Override
	public void die(DamageSource source) {
		super.die(source);
		if (level() instanceof ServerLevel level) {
			level.sendParticles(ParticleTypes.END_ROD, getX(), getY(0.5), getZ(), 300, 3, 2, 3, 0.4);
			for (BlockPos b : braziers) {
				if (level.getBlockState(b).getBlock() instanceof BrazierBlock) {
					BrazierBlock.ignite(level, b, level.getBlockState(b));
				}
			}
			dev.celestial.story.StoryEvents.onDevourerDefeated(level, this);
			record.finish(level, bossEvent.getPlayers(), dev.celestial.story.Story.DEVOURER_FLAWLESS, dev.celestial.story.Story.DEVOURER_SWIFT, SWIFT_TICKS);
		}
	}

	@Override
	public boolean causeFallDamage(double fallDistance, float multiplier, DamageSource source) {
		return false;
	}

	@Override
	protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {
	}

	@Override
	public boolean removeWhenFarAway(double distSqr) {
		return false;
	}

	@Override
	public boolean canUsePortal(boolean ignorePassenger) {
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
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.store("Home", BlockPos.CODEC, home);
		output.putInt("Phase", phase);  // без фазы после перезахода «входил» в фазу заново и гасил все жаровни
		record.save(output);
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		home = input.read("Home", BlockPos.CODEC).orElse(BlockPos.ZERO);
		phase = input.getIntOr("Phase", 1);
		record.load(input);
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return ModSounds.DEVOURER_ROAR;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.PHANTOM_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.ENDER_DRAGON_DEATH;
	}

	@Override
	public float getVoicePitch() {
		return 0.5F;
	}

	@Override
	public int getAmbientSoundInterval() {
		return 200;
	}
}
