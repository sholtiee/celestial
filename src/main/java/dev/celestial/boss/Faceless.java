package dev.celestial.boss;

import dev.celestial.chrono.TimeFlow;
import dev.celestial.registry.ModEntities;
import dev.celestial.registry.ModParticles;
import java.util.ArrayList;
import java.util.Iterator;
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
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AreaEffectCloud;
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

/**
 * Безликий — Денница, потерявший имя и облик; босс Акта V на вершине Звёздного алтаря. Бой — семь труб (Откр. 8–11):
 * каждая седьмая доля здоровья — новая труба, и он берёт силу прежних боссов.
 * 1 «Град и огонь» — метки на полу, через миг падает огненный град (Серафим). 2 «Гора огненная в море» — ледяные шипы из-под ног (Архонт).
 * 3 «Звезда Полынь» — падающие звёзды оставляют облака горечи (яд). 4 «Померкла треть светил» — волны Тьмы, он скрывается (Пожиратель).
 * 5 «Саранча из бездны» — рой слепых охотников. 6 «Четыре ангела Евфрата» — «Стой!» останавливает время (Часовщик).
 * 7 «Седьмая труба» — всё сразу; на его груди проступает утренняя звезда.
 * Трубы 1, 2, 4 и 6 переносят бой в **отражения пройденных миров** (Рай, Чертоги, Бездна, Хроноград — шаблоны `faceless/<мир>`,
 * стоят в пустоте Астрала в {@link #REFLECTION_GAP} блоках от вершины); 3, 5 и 7 — на вершине алтаря. Умереть он не может: на последней капле здоровья
 * опускается на колени у алтаря — подойди, ПКМ по нему и выбери концовку ({@link dev.celestial.story.Endings}).
 * Ранят его только игроки (прочее ×0.1).
 */
public class Faceless extends Monster {
	private static final int SWIFT_TICKS = 12 * 60 * 20;
	private static final EntityDataAccessor<Integer> PHASE = SynchedEntityData.defineId(Faceless.class, EntityDataSerializers.INT);
	private static final EntityDataAccessor<Boolean> DEFEATED = SynchedEntityData.defineId(Faceless.class, EntityDataSerializers.BOOLEAN);
	private static final EntityDataAccessor<Integer> CAST = SynchedEntityData.defineId(Faceless.class, EntityDataSerializers.INT);
	public static final String SUMMON_TAG = "celestial_faceless_summon";
	public static final double ARENA = 18.0;
	public static final int TRUMPETS = 7;

	private final BossRecord record = new BossRecord();
	private final ServerBossEvent bossEvent = new ServerBossEvent(java.util.UUID.randomUUID(), Component.translatable("entity.celestial.faceless"),
		BossEvent.BossBarColor.PURPLE, BossEvent.BossBarOverlay.NOTCHED_6);
	private BlockPos home = BlockPos.ZERO;
	/** Где сейчас бой: вершина (home) или отражение мира. */
	private BlockPos center = BlockPos.ZERO;
	/** Какие отражения уже поставлены (биты по REFLECTIONS). */
	private int placed;
	private int clock;
	private int phaseStart;
	private int sweepCooldown;
	private double orbit;

	/** Удар с неба по метке: позиция, тиков до удара, вид (0 град, 1 Полынь). */
	private record Strike(Vec3 pos, int[] left, int kind) {}

	private final List<Strike> strikes = new ArrayList<>();

	public Faceless(EntityType<? extends Faceless> type, Level level) {
		super(type, level);
		this.xpReward = 500;
		setNoGravity(true);
		bossEvent.setPlayBossMusic(true);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
			.add(Attributes.MAX_HEALTH, 1000.0)  // потолок атрибута в ванилле — 1024
			.add(Attributes.ARMOR, 16.0)
			.add(Attributes.ATTACK_DAMAGE, 12.0)
			.add(Attributes.FOLLOW_RANGE, 64.0)
			.add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
			.add(Attributes.MOVEMENT_SPEED, 0.3);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(PHASE, 1);
		builder.define(DEFEATED, false);
		builder.define(CAST, 0);
	}

	/** Трубы, что переносят бой в отражение пройденного мира: труба → шаблон. Отражения стоят в пустоте Астрала, далеко от вершины. */
	private static final String[] REFLECTIONS = {"heaven", "frozen", null, "abyss", null, "chrono", null};
	private static final int REFLECTION_GAP = 320;
	private static final int REFLECTION_R = 15;

	public void setHome(BlockPos home) {
		this.home = home.immutable();
		this.center = this.home;
	}

	/** Центр арены трубы (пол на этой высоте, как у алтаря на вершине). */
	private BlockPos arenaFor(int phase) {
		int k = phase - 1;
		return REFLECTIONS[k] == null ? home : home.offset(0, 0, REFLECTION_GAP * (k + 1));
	}

	/** Перенести бой: поставить отражение (раз), перенести бойцов и себя, вспышка и слова. */
	private void moveTo(ServerLevel level, BlockPos target, int phase, List<ServerPlayer> fighters) {
		if (target.equals(center)) {
			return;
		}
		int k = phase - 1;
		String name = REFLECTIONS[Math.max(0, Math.min(k, REFLECTIONS.length - 1))];
		if (!target.equals(home) && name != null && (placed & (1 << k)) == 0) {
			var template = level.getServer().getStructureTemplateManager().get(dev.celestial.Celestial.id("faceless/" + name));
			if (template.isEmpty()) {
				return;
			}
			BlockPos origin = target.offset(-REFLECTION_R, -2, -REFLECTION_R);
			template.get().placeInWorld(level, origin, origin, new net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings(),
				level.getRandom(), 2);
			placed |= 1 << k;
		}
		for (ServerPlayer p : fighters) {
			double a = random.nextDouble() * Math.PI * 2;
			Vec3 to = Vec3.atBottomCenterOf(target).add(Math.cos(a) * 7, 0.1, Math.sin(a) * 7);
			level.sendParticles(ParticleTypes.END_ROD, p.getX(), p.getY() + 1, p.getZ(), 30, 0.4, 0.8, 0.4, 0.05);
			p.teleport(new net.minecraft.world.level.portal.TeleportTransition(level, to, Vec3.ZERO, p.getYRot(), p.getXRot(),
				net.minecraft.world.level.portal.TeleportTransition.DO_NOTHING));
			p.resetFallDistance();
			if (!target.equals(home) && name != null) {
				p.sendSystemMessage(Component.translatable("boss.celestial.faceless.reflection." + name));
			}
		}
		strikes.clear();
		teleportTo(target.getX() + 0.5, target.getY() + 3.5, target.getZ() + 0.5);
		center = target.immutable();
		level.playSound(null, target, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 3.0F, 0.5F);
	}

	public BlockPos home() {
		return home;
	}

	public int phase() {
		return entityData.get(PHASE);
	}

	public boolean defeated() {
		return entityData.get(DEFEATED);
	}

	public int casting() {
		return entityData.get(CAST);
	}

	@Override
	protected void registerGoals() {
	}

	public List<ServerPlayer> fighters(ServerLevel level) {
		Vec3 c = Vec3.atBottomCenterOf(center.equals(BlockPos.ZERO) ? home : center);
		// в невесомости бойцы взлетают высоко — по горизонтали арена, по вертикали запас
		return level.getPlayers(p -> !p.isCreative() && !p.isSpectator() && p.isAlive()
			&& Math.hypot(p.getX() - c.x, p.getZ() - c.z) < ARENA + 6 && Math.abs(p.getY() - c.y) < 40);
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		clock++;
		if (home.equals(BlockPos.ZERO)) {
			home = blockPosition().below(3);
			center = home;
		}
		if (casting() > 0) {
			entityData.set(CAST, casting() - 1);
		}
		if (defeated()) {
			kneel(level);
			return;
		}
		record.tick(level, bossEvent.getPlayers());
		if (sweepCooldown > 0) {
			sweepCooldown--;
		}
		bossEvent.setProgress(getHealth() / getMaxHealth());
		int newPhase = Math.min(TRUMPETS, 1 + (int) ((1.0F - getHealth() / getMaxHealth()) * TRUMPETS));
		if (newPhase > phase()) {
			entityData.set(PHASE, newPhase);
			onTrumpet(level, newPhase);
		}
		List<ServerPlayer> fighters = fighters(level);
		BlockPos wanted = arenaFor(phase());
		if (!wanted.equals(center) && clock - phaseStart >= 20) {  // труба протрубила — через секунду мир меняется
			moveTo(level, wanted, phase(), fighters);
		}
		hover(fighters);
		tickStrikes(level, fighters);
		if (fighters.isEmpty()) {
			return;
		}
		int phase = phase();
		ServerPlayer target = fighters.get((clock / 80) % fighters.size());
		setTarget(target);
		if (sweepCooldown == 0) {
			for (ServerPlayer p : fighters) {
				if (p.distanceToSqr(this) < 4.5 * 4.5) {
					sweep(level, fighters);
					break;
				}
			}
		}
		int boltEvery = phase >= 7 ? 25 : 40;
		if (clock % boltEvery == 0) {
			bolt(level, target);
		}
		int t = clock - phaseStart;
		switch (phase) {
			case 1 -> {
				if (t % 20 == 0) {
					hail(fighters, 0, 3);
				}
			}
			case 2 -> {
				if (t % 45 == 0) {
					spikes(level, fighters);
				}
			}
			case 3 -> {
				if (t % 35 == 0) {
					hail(fighters, 1, 2);
				}
			}
			case 4 -> {
				if (t % 100 == 0) {
					darkness(level, fighters);
				}
			}
			case 5 -> {
				if (t % 300 == 25) {  // после переноса на вершину
					locusts(level);
				}
			}
			case 6 -> {
				if (t % 300 == 270) {
					warn(level, fighters);
				} else if (t % 300 == 0 && t > 0) {
					stopTime(level, fighters);
				}
			}
			default -> {  // седьмая — всё сразу, реже
				if (t % 30 == 0) {
					hail(fighters, t % 60 == 0 ? 0 : 1, 2);
				}
				if (t % 90 == 45) {
					spikes(level, fighters);
				}
				if (t % 400 == 200) {
					darkness(level, fighters);
				}
				if (t % 400 == 0) {
					locusts(level);
				}
			}
		}
	}

	private void hover(List<ServerPlayer> fighters) {
		orbit += 0.008 + phase() * 0.001;
		Vec3 c = Vec3.atBottomCenterOf(center);
		Vec3 wanted = new Vec3(c.x + Math.cos(orbit) * 6, c.y + 3.5 + Math.sin(clock * 0.04) * 0.6, c.z + Math.sin(orbit) * 6);
		Vec3 delta = wanted.subtract(position());
		setDeltaMovement(getDeltaMovement().scale(0.75).add(delta.normalize().scale(Math.min(0.12, delta.length() * 0.05))));
		LivingEntity look = getTarget();
		if (look != null) {
			double dx = look.getX() - getX(), dz = look.getZ() - getZ();
			setYRot((float) (Mth.atan2(dz, dx) * Mth.RAD_TO_DEG) - 90.0F);
			yBodyRot = getYRot();
			yHeadRot = getYRot();
		}
	}

	/** Повержен: медленно опускается к алтарю, тьма стекает с него, утренняя звезда светит. */
	private void kneel(ServerLevel level) {
		Vec3 c = Vec3.atBottomCenterOf(home).add(0, 1.0, 0);
		Vec3 delta = c.subtract(position());
		setDeltaMovement(delta.scale(0.05));
		if (clock % 4 == 0) {
			level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 2.0, getZ(), 2, 0.4, 0.6, 0.4, 0.01);
			level.sendParticles(ModParticles.SHADOW, getX(), getY() + 1.0, getZ(), 3, 0.6, 0.8, 0.6, 0.01);
		}
	}

	private void onTrumpet(ServerLevel level, int phase) {
		phaseStart = clock;
		entityData.set(CAST, 30);
		level.playSound(null, blockPosition(), SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 6.0F, 0.6F + phase * 0.05F);
		bossEvent.setColor(phase >= 7 ? BossEvent.BossBarColor.WHITE : phase >= 4 ? BossEvent.BossBarColor.RED : BossEvent.BossBarColor.PURPLE);
		for (ServerPlayer p : bossEvent.getPlayers()) {
			p.sendSystemMessage(Component.translatable("boss.celestial.faceless.trumpet" + phase));
		}
		BossIntro.phase(bossEvent.getPlayers(), "faceless", phase, phase >= 7 ? ChatFormatting.WHITE : ChatFormatting.LIGHT_PURPLE);
	}

	private void sweep(ServerLevel level, List<ServerPlayer> fighters) {
		sweepCooldown = 40;
		entityData.set(CAST, 10);
		playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 2.0F, 0.5F);
		for (ServerPlayer p : fighters) {
			if (p.distanceToSqr(this) < 4.5 * 4.5 && p.hurtServer(level, damageSources().mobAttack(this), TimeFlow.scale(p) <= 0 ? 5.0F : 10.0F)) {
				Vec3 push = p.position().subtract(position()).multiply(1, 0, 1).normalize().scale(1.0);
				p.push(push.x, 0.4, push.z);
				p.syncVelocity = true;
				p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 40, 0));
			}
		}
	}

	private void bolt(ServerLevel level, LivingEntity target) {
		VoidBolt b = new VoidBolt(ModEntities.VOID_BOLT, this, level);
		b.setPos(getX(), getEyeY() - 0.4, getZ());
		Vec3 aim = target.getEyePosition().subtract(b.position()).normalize();
		b.shoot(aim.x, aim.y, aim.z, 1.1F, 2.0F);
		level.addFreshEntity(b);
		playSound(SoundEvents.ILLUSIONER_CAST_SPELL, 1.5F, 0.6F);
	}

	/** Метки на полу у бойцов; через 25 тиков — удар с неба. */
	private void hail(List<ServerPlayer> fighters, int kind, int perPlayer) {
		for (ServerPlayer p : fighters) {
			for (int i = 0; i < perPlayer; i++) {
				double dx = i == 0 ? 0 : (random.nextDouble() * 2 - 1) * 4;
				double dz = i == 0 ? 0 : (random.nextDouble() * 2 - 1) * 4;
				strikes.add(new Strike(new Vec3(p.getX() + dx, center.getY() + 0.05, p.getZ() + dz), new int[] {25}, kind));
			}
		}
	}

	private void tickStrikes(ServerLevel level, List<ServerPlayer> fighters) {
		for (Iterator<Strike> it = strikes.iterator(); it.hasNext(); ) {
			Strike s = it.next();
			int left = --s.left()[0];
			if (left > 0) {
				if (left % 3 == 0) {  // метка — кольцо на полу
					for (int k = 0; k < 10; k++) {
						double a = k * Math.PI / 5;
						level.sendParticles(s.kind() == 0 ? ParticleTypes.FLAME : ParticleTypes.WITCH, s.pos().x + Math.cos(a) * 1.6, s.pos().y,
							s.pos().z + Math.sin(a) * 1.6, 1, 0, 0, 0, 0);
					}
				}
				if (left < 10) {  // падает
					level.sendParticles(s.kind() == 0 ? ParticleTypes.LAVA : ParticleTypes.END_ROD, s.pos().x, s.pos().y + left * 1.2, s.pos().z, 2, 0.1, 0.1, 0.1, 0);
				}
				continue;
			}
			it.remove();
			level.sendParticles(ParticleTypes.EXPLOSION, s.pos().x, s.pos().y + 0.3, s.pos().z, 1, 0, 0, 0, 0);
			level.playSound(null, BlockPos.containing(s.pos()), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.2F, 1.3F);
			for (ServerPlayer p : fighters) {
				if (p.position().distanceTo(s.pos()) < 2.0) {
					p.hurtServer(level, damageSources().indirectMagic(this, this), 7.0F);
					if (s.kind() == 0) {
						p.igniteForSeconds(4.0F);
					}
				}
			}
			if (s.kind() == 1) {  // Полынь: облако горечи
				AreaEffectCloud cloud = new AreaEffectCloud(level, s.pos().x, s.pos().y, s.pos().z);
				cloud.setRadius(2.5F);
				cloud.setDuration(100);
				cloud.setRadiusPerTick(-0.01F);
				cloud.addEffect(new MobEffectInstance(MobEffects.POISON, 80, 0));
				cloud.setOwner(this);
				level.addFreshEntity(cloud);
			}
		}
	}

	/** Вторая труба: шипы Архонта под ногами. */
	private void spikes(ServerLevel level, List<ServerPlayer> fighters) {
		for (ServerPlayer p : fighters) {
			IceSpike spike = ModEntities.ICE_SPIKE.create(level, EntitySpawnReason.MOB_SUMMONED);
			if (spike != null) {
				spike.snapTo(p.getX(), center.getY(), p.getZ(), random.nextFloat() * 360, 0);
				spike.setup(this, 9.0F);
				level.addFreshEntity(spike);
			}
		}
	}

	/** Четвёртая труба: волна Тьмы, он скрывается на 3 с. */
	private void darkness(ServerLevel level, List<ServerPlayer> fighters) {
		entityData.set(CAST, 20);
		for (ServerPlayer p : fighters) {
			p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 80, 0));
			p.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 30, 0));
		}
		addEffect(new MobEffectInstance(MobEffects.INVISIBILITY, 60, 0, false, false));
		level.sendParticles(ModParticles.SHADOW, getX(), getY() + 1, getZ(), 200, ARENA / 2, 2, ARENA / 2, 0.02);
		level.playSound(null, blockPosition(), SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 3.0F, 0.5F);
	}

	/** Пятая труба: саранча из бездны — слепые охотники (не больше 6 живых). */
	private void locusts(ServerLevel level) {
		int alive = level.getEntitiesOfClass(Mob.class, getBoundingBox().inflate(ARENA + 8), m -> m.entityTags().contains(SUMMON_TAG)).size();
		for (int i = alive; i < 6; i++) {
			Mob m = ModEntities.BLIND_HUNTER.create(level, EntitySpawnReason.MOB_SUMMONED);
			if (m == null) {
				continue;
			}
			double a = random.nextDouble() * Math.PI * 2;
			m.snapTo(center.getX() + 0.5 + Math.cos(a) * 9, center.getY(), center.getZ() + 0.5 + Math.sin(a) * 9, random.nextFloat() * 360, 0);
			m.addTag(SUMMON_TAG);
			m.addTag(dev.celestial.world.abyss.Darkness.NO_REPEL);
			level.addFreshEntity(m);
			level.sendParticles(ModParticles.SHADOW, m.getX(), m.getY() + 1, m.getZ(), 20, 0.3, 0.6, 0.3, 0.02);
		}
	}

	private void warn(ServerLevel level, List<ServerPlayer> fighters) {
		for (ServerPlayer p : fighters) {
			p.sendOverlayMessage(Component.translatable("boss.celestial.clockmaker.tick").withStyle(ChatFormatting.LIGHT_PURPLE));
		}
		level.playSound(null, blockPosition(), SoundEvents.NOTE_BLOCK_HAT.value(), SoundSource.HOSTILE, 3.0F, 0.5F);
	}

	/** Шестая труба: «Стой!» Часовщика — 2 с время стоит для всех, кроме него и его снарядов. */
	private void stopTime(ServerLevel level, List<ServerPlayer> fighters) {
		TimeFlow.stop(level, Vec3.atBottomCenterOf(center), 40, 40, true, this);  // шар 40 — накрывает и взлетевших в невесомости
		for (ServerPlayer p : fighters) {
			BossIntro.title(p, Component.translatable("boss.celestial.clockmaker.stop").withStyle(ChatFormatting.LIGHT_PURPLE, ChatFormatting.BOLD),
				Component.empty(), 30);
			bolt(level, p);
		}
		level.playSound(null, blockPosition(), SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 4.0F, 0.3F);
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (defeated() && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
			return false;
		}
		if (source.is(DamageTypeTags.IS_FALL) || source.is(DamageTypeTags.IS_DROWNING) || source.is(DamageTypeTags.IS_FIRE)) {
			return false;
		}
		if (!(source.getEntity() instanceof Player) && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
			amount *= 0.1F;
		}
		record.dealt(source);
		if (!source.is(DamageTypeTags.BYPASSES_INVULNERABILITY) && getHealth() - amount <= 1.0F) {
			// умереть он не может: на последней капле — на колени
			boolean hit = super.hurtServer(level, source, Math.max(0, getHealth() - 1.0F));
			setHealth(1.0F);
			defeat(level);
			return hit;
		}
		return super.hurtServer(level, source, amount);
	}

	private void defeat(ServerLevel level) {
		if (defeated()) {
			return;
		}
		entityData.set(DEFEATED, true);
		entityData.set(PHASE, TRUMPETS);
		moveTo(level, home, TRUMPETS, fighters(level));
		strikes.clear();
		for (Mob m : level.getEntitiesOfClass(Mob.class, getBoundingBox().inflate(ARENA + 8), m -> m.entityTags().contains(SUMMON_TAG))) {
			level.sendParticles(ModParticles.SHADOW, m.getX(), m.getY(0.5), m.getZ(), 20, 0.4, 0.6, 0.4, 0.05);
			m.discard();
		}
		for (VoidBolt b : level.getEntitiesOfClass(VoidBolt.class, getBoundingBox().inflate(ARENA + 8))) {
			b.discard();
		}
		bossEvent.setName(Component.translatable("boss.celestial.faceless.defeated"));
		bossEvent.setColor(BossEvent.BossBarColor.WHITE);
		bossEvent.setProgress(0.0F);
		level.playSound(null, blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 4.0F, 0.5F);
		for (ServerPlayer p : bossEvent.getPlayers()) {
			p.sendSystemMessage(Component.translatable("boss.celestial.faceless.kneels"));
			BossIntro.title(p, Component.translatable("boss.celestial.faceless.kneels_title").withStyle(ChatFormatting.WHITE),
				Component.translatable("boss.celestial.faceless.kneels_sub").withStyle(ChatFormatting.ITALIC), 80);
		}
		record.finish(level, bossEvent.getPlayers(), dev.celestial.story.Story.FACELESS_FLAWLESS, dev.celestial.story.Story.FACELESS_SWIFT, SWIFT_TICKS);
	}

	/** Повергнутый — подойти и коснуться: выбор концовки. */
	@Override
	protected InteractionResult mobInteract(Player player, InteractionHand hand) {
		if (defeated() && player instanceof ServerPlayer sp && hand == InteractionHand.MAIN_HAND) {
			dev.celestial.story.Endings.offer(sp, this);
			return InteractionResult.SUCCESS;
		}
		return super.mobInteract(player, hand);
	}

	/** Конец боя: концовка выбрана — Безликий уходит светом или тьмой. */
	public void release(ServerLevel level, boolean light) {
		level.sendParticles(light ? ParticleTypes.END_ROD : ModParticles.SHADOW, getX(), getY(1.0), getZ(), 400, 2, 3, 2, 0.3);
		level.playSound(null, blockPosition(), light ? SoundEvents.BEACON_ACTIVATE : SoundEvents.WITHER_DEATH, SoundSource.HOSTILE, 4.0F, light ? 1.4F : 0.6F);
		bossEvent.removeAllPlayers();
		discard();
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (level().isClientSide()) {
			if (random.nextInt(2) == 0) {
				level().addParticle(ModParticles.SHADOW, getRandomX(1.4), getRandomY(), getRandomZ(1.4), 0, 0.02, 0);
			}
			if (phase() >= TRUMPETS && random.nextInt(3) == 0) {  // утренняя звезда сквозь тьму
				level().addParticle(ModParticles.STARLIGHT, getX(), getY() + 2.6, getZ(), (random.nextDouble() - 0.5) * 0.1, 0.02,
					(random.nextDouble() - 0.5) * 0.1);
			}
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
		output.store("Center", BlockPos.CODEC, center);
		output.putInt("Placed", placed);
		output.putInt("Phase", phase());
		output.putBoolean("Defeated", defeated());
		record.save(output);
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		home = input.read("Home", BlockPos.CODEC).orElse(BlockPos.ZERO);
		center = input.read("Center", BlockPos.CODEC).orElse(home);
		placed = input.getIntOr("Placed", 0);
		entityData.set(PHASE, input.getIntOr("Phase", 1));
		entityData.set(DEFEATED, input.getBooleanOr("Defeated", false));
		record.load(input);
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return SoundEvents.SCULK_SHRIEKER_SHRIEK;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.WARDEN_HURT;
	}

	@Override
	public float getVoicePitch() {
		return 0.6F;
	}
}
