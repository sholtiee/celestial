package dev.celestial.boss;

import dev.celestial.chrono.PendulumBlock;
import dev.celestial.chrono.TimeFlow;
import dev.celestial.registry.ModEntities;
import dev.celestial.registry.ModParticles;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.ChatFormatting;
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
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * Часовщик-Механоид — хранитель хода Хронограда, босс Акта IV. Сидит на колесе-престоле с очами (офаним) над циферблатом арены.
 * Безликий заставил его держать стрелки мира на «последней минуте до падения».
 * Фазы: 1 «Ход» — взмахи руками-стрелками вблизи, шестерни катятся по полу к бойцам.
 * 2 «Остановка» (≤66%) — каждые 15 с: «Тик… так…» (1,5 с на укрытие) и «Стой!» — время стоит для всех, кроме него, 2 с; шестерни катятся.
 * 3 «Перемотка» (≤33%) — заводит древние маятники арены; пока хоть один качается, каждые 10 с переводит себе здоровье на 10 с назад
 * и не опускается ниже 15%. Остановить маятник — Камертоном (ПКМ). Ранят его только игроки (прочее — ×0.1).
 */
public class Clockmaker extends Monster {
	private static final int SWIFT_TICKS = 9 * 60 * 20;
	private static final EntityDataAccessor<Integer> PHASE = SynchedEntityData.defineId(Clockmaker.class, EntityDataSerializers.INT);
	private static final EntityDataAccessor<Integer> SWEEP = SynchedEntityData.defineId(Clockmaker.class, EntityDataSerializers.INT);
	private static final EntityDataAccessor<Integer> WARN = SynchedEntityData.defineId(Clockmaker.class, EntityDataSerializers.INT);
	public static final double ARENA = 16.0;
	private static final int STOP_EVERY = 300;
	private static final int WARN_TICKS = 30;
	private static final int STOP_TICKS = 40;
	private static final float FLOOR = 0.15F;

	private final BossRecord record = new BossRecord();
	private final ServerBossEvent bossEvent = new ServerBossEvent(java.util.UUID.randomUUID(), Component.translatable("entity.celestial.clockmaker"),
		BossEvent.BossBarColor.YELLOW, BossEvent.BossBarOverlay.NOTCHED_12);
	private BlockPos home = BlockPos.ZERO;
	private int clock;
	private int sweepCooldown;
	private double orbit;
	private int phase2Start = -1;
	private int phase3Start = -1;
	/** Здоровье раз в секунду за последние 11 с (кольцо) — для перемотки. */
	private final float[] history = new float[11];
	private int historyIdx;
	private boolean pendulumsSwinging;
	private int deflectMsgCooldown;

	public Clockmaker(EntityType<? extends Clockmaker> type, Level level) {
		super(type, level);
		this.xpReward = 300;
		setNoGravity(true);
		bossEvent.setPlayBossMusic(true);
		java.util.Arrays.fill(history, -1);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
			.add(Attributes.MAX_HEALTH, 800.0)
			.add(Attributes.ARMOR, 14.0)
			.add(Attributes.ATTACK_DAMAGE, 12.0)
			.add(Attributes.FOLLOW_RANGE, 48.0)
			.add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
			.add(Attributes.MOVEMENT_SPEED, 0.3);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(PHASE, 1);
		builder.define(SWEEP, 0);
		builder.define(WARN, 0);
	}

	public void setHome(BlockPos home) {
		this.home = home.immutable();
	}

	public int phase() {
		return entityData.get(PHASE);
	}

	/** Тики взмаха руками-стрелками (для анимации). */
	public int sweeping() {
		return entityData.get(SWEEP);
	}

	/** Тики «Тик… так…» перед остановкой (для анимации: циферблат горит, стрелки замирают). */
	public int warning() {
		return entityData.get(WARN);
	}

	@Override
	protected void registerGoals() {
	}

	private List<ServerPlayer> fighters(ServerLevel level) {
		Vec3 c = Vec3.atBottomCenterOf(home);
		return level.getPlayers(p -> !p.isCreative() && !p.isSpectator() && p.isAlive() && p.position().distanceTo(c) < ARENA);
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		record.tick(level, bossEvent.getPlayers());
		clock++;
		if (home.equals(BlockPos.ZERO)) {
			home = blockPosition().below(2);
		}
		if (sweepCooldown > 0) {
			sweepCooldown--;
		}
		if (sweeping() > 0) {
			entityData.set(SWEEP, sweeping() - 1);
		}
		if (deflectMsgCooldown > 0) {
			deflectMsgCooldown--;
		}
		if (clock % 20 == 0) {
			history[historyIdx] = getHealth();
			historyIdx = (historyIdx + 1) % history.length;
		}
		if (clock % 10 == 0) {
			pendulumsSwinging = !pendulums(level, true).isEmpty();
		}
		bossEvent.setProgress(getHealth() / getMaxHealth());
		int newPhase = getHealth() > getMaxHealth() * 0.66F ? 1 : getHealth() > getMaxHealth() * 0.33F ? 2 : 3;
		if (newPhase > phase()) {
			entityData.set(PHASE, newPhase);
			onPhase(level, newPhase);
		}
		int phase = phase();
		List<ServerPlayer> fighters = fighters(level);
		hover(fighters);
		if (fighters.isEmpty()) {
			return;
		}
		ServerPlayer target = fighters.get((clock / 100) % fighters.size());
		setTarget(target);
		if (sweepCooldown == 0) {
			for (ServerPlayer p : fighters) {
				if (p.distanceToSqr(this) < 4.8 * 4.8) {
					sweep(level, fighters);
					break;
				}
			}
		}
		int gearEvery = phase == 1 ? 60 : phase == 2 ? 50 : 40;
		if (clock % gearEvery == 0) {
			rollGears(level, target, phase == 1 ? 1 : phase == 2 ? 3 : 5);
		}
		if (phase >= 2) {
			if (phase2Start < 0) {
				phase2Start = clock;
			}
			int t = (clock - phase2Start) % STOP_EVERY;
			if (t == STOP_EVERY - WARN_TICKS) {
				warn(level, fighters);
			} else if (t == 0 && clock != phase2Start) {
				stopTime(level, fighters);
			} else if (t == STOP_EVERY / 2) {
				summonBeetles(level);
			}
			if (warning() > 0) {
				entityData.set(WARN, warning() - 1);
			}
		}
		if (phase == 3) {
			if (phase3Start < 0) {
				phase3Start = clock;
			}
			if ((clock - phase3Start) % 200 == 100 && pendulumsSwinging) {
				rewind(level);
			}
		}
	}

	/** Колесо-престол медленно кружит над циферблатом на высоте ~2.5 блока, Часовщик смотрит на бойца. */
	private void hover(List<ServerPlayer> fighters) {
		orbit += phase() == 3 ? 0.016 : 0.01;
		Vec3 c = Vec3.atBottomCenterOf(home);
		double r = phase() == 1 ? 3.5 : 5.5;
		Vec3 wanted = new Vec3(c.x + Math.cos(orbit) * r, c.y + 2.4 + Math.sin(clock * 0.05) * 0.3, c.z + Math.sin(orbit) * r);
		Vec3 delta = wanted.subtract(position());
		setDeltaMovement(getDeltaMovement().scale(0.75).add(delta.normalize().scale(Math.min(0.1, delta.length() * 0.05))));
		LivingEntity look = getTarget();
		if (look != null) {
			double dx = look.getX() - getX(), dz = look.getZ() - getZ();
			setYRot((float) (Mth.atan2(dz, dx) * Mth.RAD_TO_DEG) - 90.0F);
			yBodyRot = getYRot();
			yHeadRot = getYRot();
		}
	}

	private void onPhase(ServerLevel level, int phase) {
		playSound(SoundEvents.BELL_BLOCK, 4.0F, 0.5F);
		bossEvent.setColor(phase == 3 ? BossEvent.BossBarColor.RED : BossEvent.BossBarColor.YELLOW);
		for (ServerPlayer p : bossEvent.getPlayers()) {
			p.sendSystemMessage(Component.translatable("boss.celestial.clockmaker.phase" + phase));
		}
		BossIntro.phase(bossEvent.getPlayers(), "clockmaker", phase, phase == 3 ? ChatFormatting.RED : ChatFormatting.GOLD);
		if (phase == 3) {
			// перезавод: все древние маятники арены снова качаются — их надо остановить заново
			for (BlockPos p : pendulums(level, false)) {
				BlockState st = level.getBlockState(p);
				level.setBlock(p, st.setValue(PendulumBlock.SWINGING, true), Block.UPDATE_ALL);
				level.sendParticles(ModParticles.CHRONO_HASTE, p.getX() + 0.5, p.getY() + 1.2, p.getZ() + 0.5, 30, 0.4, 0.6, 0.4, 0.08);
			}
			pendulumsSwinging = true;
		}
	}

	/** Взмах всеми четырьмя руками-стрелками: удар и отброс всем вблизи. */
	private void sweep(ServerLevel level, List<ServerPlayer> fighters) {
		entityData.set(SWEEP, 14);
		sweepCooldown = phase() == 3 ? 30 : 40;
		playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 2.0F, 0.6F);
		level.sendParticles(ParticleTypes.SWEEP_ATTACK, getX(), getY() + 1.2, getZ(), 6, 2.2, 0.4, 2.2, 0.0);
		for (ServerPlayer p : fighters) {
			if (p.distanceToSqr(this) < 4.8 * 4.8) {
				float dmg = TimeFlow.scale(p) <= 0 ? 5.0F : 10.0F;  // по застывшему — вполсилы
				if (p.hurtServer(level, damageSources().mobAttack(this), dmg)) {
					Vec3 push = p.position().subtract(position()).multiply(1, 0, 1).normalize().scale(1.1);
					p.push(push.x, 0.35, push.z);
					p.syncVelocity = true;
				}
			}
		}
	}

	/** Шестерни: n штук веером к цели, катятся по полу. */
	private void rollGears(ServerLevel level, LivingEntity target, int n) {
		Vec3 base = target.position().subtract(position()).multiply(1, 0, 1).normalize();
		if (base.lengthSqr() < 1.0E-4) {
			base = new Vec3(1, 0, 0);
		}
		double spread = n == 1 ? 0 : Math.toRadians(16);
		for (int i = 0; i < n; i++) {
			double a = (i - (n - 1) / 2.0) * spread;
			Vec3 dir = new Vec3(base.x * Math.cos(a) - base.z * Math.sin(a), 0, base.x * Math.sin(a) + base.z * Math.cos(a));
			ClockGear gear = new ClockGear(ModEntities.CLOCK_GEAR, this, level);
			gear.setPos(getX() + dir.x * 1.5, home.getY() + 1.02, getZ() + dir.z * 1.5);
			gear.setDeltaMovement(dir.scale(0.42));
			level.addFreshEntity(gear);
		}
		playSound(SoundEvents.CHAIN_PLACE, 2.0F, 0.6F);
	}

	private void warn(ServerLevel level, List<ServerPlayer> fighters) {
		entityData.set(WARN, WARN_TICKS);
		for (ServerPlayer p : fighters) {
			p.sendOverlayMessage(Component.translatable("boss.celestial.clockmaker.tick").withStyle(ChatFormatting.GOLD));
		}
		level.playSound(null, blockPosition(), SoundEvents.NOTE_BLOCK_HAT.value(), SoundSource.HOSTILE, 3.0F, 0.5F);
	}

	/** «Стой!»: 2 с время стоит для всех в арене, кроме Часовщика и его шестерён. */
	private void stopTime(ServerLevel level, List<ServerPlayer> fighters) {
		TimeFlow.stop(level, Vec3.atBottomCenterOf(home), ARENA + 4, STOP_TICKS, true, this);
		for (ServerPlayer p : fighters) {
			BossIntro.title(p, Component.translatable("boss.celestial.clockmaker.stop").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD),
				Component.empty(), 30);
			BossIntro.shake(p, 1.2F, 10);
		}
		level.playSound(null, blockPosition(), dev.celestial.registry.ModSounds.CLOCKMAKER_STOP, SoundSource.HOSTILE, 4.0F, 1.0F);
		level.sendParticles(ModParticles.CHRONO_LAG, getX(), getY() + 1, getZ(), 120, ARENA / 2, 1.5, ARENA / 2, 0.0);
		for (ServerPlayer p : fighters) {
			rollGears(level, p, 2);
		}
	}

	/** Ф2+: из-под циферблата выбегают подзаведённые жуки-заводняки (не больше 6 живых на арене). */
	private void summonBeetles(ServerLevel level) {
		int alive = level.getEntitiesOfClass(dev.celestial.entity.WinderBeetle.class, getBoundingBox().inflate(ARENA + 4)).size();
		for (int i = alive; i < Math.min(6, alive + 3); i++) {
			dev.celestial.entity.WinderBeetle beetle = dev.celestial.registry.ModEntities.WINDER_BEETLE.create(level, EntitySpawnReason.MOB_SUMMONED);
			if (beetle == null) {
				continue;
			}
			double a = random.nextDouble() * Math.PI * 2;
			double r = 3 + random.nextDouble() * (ARENA - 5);
			beetle.snapTo(home.getX() + 0.5 + Math.cos(a) * r, home.getY() + 1, home.getZ() + 0.5 + Math.sin(a) * r, (float) Math.toDegrees(a), 0);
			beetle.addTag(dev.celestial.world.abyss.Darkness.NO_REPEL);
			beetle.windUp(dev.celestial.entity.WinderBeetle.WOUND_TICKS);
			level.addFreshEntity(beetle);
			level.sendParticles(ParticleTypes.SMOKE, beetle.getX(), beetle.getY() + 0.3, beetle.getZ(), 8, 0.2, 0.1, 0.2, 0.02);
		}
	}

	/** Перемотка: здоровье — каким было 10 с назад (если тогда было больше). */
	private void rewind(ServerLevel level) {
		float past = history[historyIdx];  // самая старая запись кольца — ~10 с назад
		if (past <= getHealth()) {
			return;
		}
		setHealth(past);
		level.sendParticles(ParticleTypes.REVERSE_PORTAL, getX(), getY() + 1.5, getZ(), 80, 1.2, 1.5, 1.2, 0.1);
		level.playSound(null, blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3.0F, 0.6F);
		for (ServerPlayer p : bossEvent.getPlayers()) {
			p.sendSystemMessage(Component.translatable("boss.celestial.clockmaker.rewind"));
		}
	}

	/** Древние маятники арены ({@code sealed}); только качающиеся — если {@code swinging}. */
	public List<BlockPos> pendulums(ServerLevel level, boolean swinging) {
		List<BlockPos> out = new ArrayList<>();
		int r = (int) ARENA;
		for (BlockPos p : BlockPos.betweenClosed(home.offset(-r, -2, -r), home.offset(r, 10, r))) {
			BlockState st = level.getBlockState(p);
			if (st.getBlock() instanceof PendulumBlock && st.getValue(PendulumBlock.SEALED) && (!swinging || st.getValue(PendulumBlock.SWINGING))) {
				out.add(p.immutable());
			}
		}
		return out;
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (source.is(DamageTypeTags.IS_FALL) || source.is(DamageTypeTags.IS_DROWNING) || source.is(DamageTypeTags.IS_FIRE)) {
			return false;
		}
		if (!(source.getEntity() instanceof Player) && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
			amount *= 0.1F;
		}
		if (phase() == 3 && pendulumsSwinging && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
			float floor = getMaxHealth() * FLOOR;
			amount = Math.min(amount, getHealth() - floor);
			if (amount <= 0) {
				if (deflectMsgCooldown == 0 && source.getEntity() instanceof ServerPlayer p) {
					p.sendOverlayMessage(Component.translatable("boss.celestial.clockmaker.held").withStyle(ChatFormatting.GOLD));
					deflectMsgCooldown = 40;
				}
				playSound(SoundEvents.ANVIL_LAND, 1.0F, 1.6F);
				return false;
			}
		}
		record.dealt(source);
		return super.hurtServer(level, source, amount);
	}

	@Override
	public void die(DamageSource source) {
		super.die(source);
		if (level() instanceof ServerLevel level) {
			for (BlockPos p : pendulums(level, false)) {
				level.setBlock(p, level.getBlockState(p).setValue(PendulumBlock.SWINGING, false), Block.UPDATE_ALL);
			}
			for (ClockGear g : level.getEntitiesOfClass(ClockGear.class, getBoundingBox().inflate(ARENA + 8))) {
				g.discard();
			}
			level.sendParticles(ModParticles.CHRONO_HASTE, getX(), getY(0.5), getZ(), 300, 3, 3, 3, 0.4);
			level.sendParticles(ParticleTypes.END_ROD, getX(), getY(0.5), getZ(), 200, 4, 3, 4, 0.3);
			dev.celestial.story.StoryEvents.onClockmakerDefeated(level, this, home);
			record.finish(level, bossEvent.getPlayers(), dev.celestial.story.Story.CLOCKMAKER_FLAWLESS, dev.celestial.story.Story.CLOCKMAKER_SWIFT,
				SWIFT_TICKS);
		}
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (level().isClientSide() && random.nextInt(3) == 0) {
			double a = random.nextDouble() * Math.PI * 2;
			level().addParticle(phase() == 3 ? ModParticles.CHRONO_LAG : ModParticles.CHRONO_HASTE,
				getX() + Math.cos(a) * 1.6, getY() + 0.4, getZ() + Math.sin(a) * 1.6, 0, 0.02, 0);
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
		output.putInt("Phase", phase());
		record.save(output);
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		home = input.read("Home", BlockPos.CODEC).orElse(BlockPos.ZERO);
		entityData.set(PHASE, input.getIntOr("Phase", 1));
		record.load(input);
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return SoundEvents.NOTE_BLOCK_HAT.value();
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.ANVIL_PLACE;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.IRON_GOLEM_DEATH;
	}

	@Override
	public float getVoicePitch() {
		return 0.5F;
	}
}
