package dev.celestial.boss;

import dev.celestial.data.CelestialData;
import dev.celestial.registry.ModBlocks;
import dev.celestial.registry.ModEntities;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
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
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * Морозный Архонт — тюремщик Инии, босс Акта III. Парит над ареной цитадели в кольце ледяных осколков.
 * Фазы: 1 «Шипы» — метки инея на земле, через миг из них вырастают шипы; залпы ледяных осколков; «волна стужи» вблизи.
 * 2 «Метель» (≤70%) — туман и снег на арене, тепло тает быстрее, призыв стражей и духов, рывки сквозь метель.
 * 3 «Ледяная тюрьма» (≤35%) — вмораживает игрока в глыбу: разбей лёд изнутри, пока Архонт не обрушил приговор.
 * Ранят его только игроки (прочее — ×0.1): арену не обойти лавой и ловушками.
 */
public class FrostArchon extends Monster {
	private static final EntityDataAccessor<Integer> PHASE = SynchedEntityData.defineId(FrostArchon.class, EntityDataSerializers.INT);
	private static final EntityDataAccessor<Integer> CAST = SynchedEntityData.defineId(FrostArchon.class, EntityDataSerializers.INT);
	public static final String SUMMON_TAG = "celestial_archon_summon";
	private static final double ARENA = 17.0;
	private static final int PRISON_TIME = 70;

	private final ServerBossEvent bossEvent = new ServerBossEvent(java.util.UUID.randomUUID(), Component.translatable("entity.celestial.frost_archon"),
		BossEvent.BossBarColor.BLUE, BossEvent.BossBarOverlay.NOTCHED_10);
	private BlockPos home = BlockPos.ZERO;
	private int clock;
	private int novaCooldown;
	private double orbit;
	/** Тик входа в 3-ю фазу: первая тюрьма через 3 с после него, дальше каждые 10 с. */
	private int phase3Start = -1;

	/** Тюрьма: игрок, блоки льда вокруг него и сколько тиков осталось до приговора. */
	private record Prison(ServerPlayer player, List<BlockPos> blocks, BlockPos center, int[] left) {}

	private final List<Prison> prisons = new ArrayList<>();

	public FrostArchon(EntityType<? extends FrostArchon> type, Level level) {
		super(type, level);
		this.xpReward = 250;
		setNoGravity(true);
		bossEvent.setPlayBossMusic(true);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
			.add(Attributes.MAX_HEALTH, 600.0)
			.add(Attributes.ARMOR, 12.0)
			.add(Attributes.ATTACK_DAMAGE, 10.0)
			.add(Attributes.FOLLOW_RANGE, 48.0)
			.add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
			.add(Attributes.MOVEMENT_SPEED, 0.3);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(PHASE, 1);
		builder.define(CAST, 0);
	}

	public void setHome(BlockPos home) {
		this.home = home.immutable();
	}

	public int phase() {
		return entityData.get(PHASE);
	}

	/** Тики «заклинания» (руки и скипетр подняты) — для анимации. */
	public int casting() {
		return entityData.get(CAST);
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
		clock++;
		if (home.equals(BlockPos.ZERO)) {
			home = blockPosition().below(3);
		}
		if (novaCooldown > 0) {
			novaCooldown--;
		}
		if (casting() > 0) {
			entityData.set(CAST, casting() - 1);
		}
		bossEvent.setProgress(getHealth() / getMaxHealth());
		int newPhase = getHealth() > getMaxHealth() * 0.7F ? 1 : getHealth() > getMaxHealth() * 0.35F ? 2 : 3;
		if (newPhase > phase()) {
			entityData.set(PHASE, newPhase);
			onPhase(level, newPhase);
		}
		int phase = phase();
		List<ServerPlayer> fighters = fighters(level);
		hover(fighters);
		tickPrisons(level);
		if (fighters.isEmpty()) {
			return;
		}
		ServerPlayer target = fighters.get((clock / 100) % fighters.size());
		setTarget(target);
		int spikeEvery = phase == 1 ? 70 : phase == 2 ? 60 : 50;
		int volleyEvery = phase == 1 ? 50 : phase == 2 ? 45 : 40;
		if (clock % spikeEvery == 0) {
			spikes(level, fighters);
		} else if (clock % volleyEvery == volleyEvery / 2) {
			volley(level, target);
		}
		if (novaCooldown == 0) {
			for (ServerPlayer p : fighters) {
				if (p.distanceToSqr(this) < 4.0 * 4.0) {
					nova(level);
					break;
				}
			}
		}
		if (phase >= 2) {
			blizzard(level, fighters);
			if (clock % 400 == 0) {
				summon(level);
			}
			if (clock % 160 == 80) {
				blink(level);
			}
		}
		if (phase == 3) {
			if (phase3Start < 0) {
				phase3Start = clock;
			}
			if ((clock - phase3Start) % 200 == 60) {
				imprison(level, fighters);
			}
		}
	}

	/** Парит по кругу над ареной на высоте 2.5–3.5, смотрит на ближайшего бойца. */
	private void hover(List<ServerPlayer> fighters) {
		orbit += phase() == 3 ? 0.02 : 0.012;
		Vec3 c = Vec3.atBottomCenterOf(home);
		Vec3 wanted = new Vec3(c.x + Math.cos(orbit) * 6, c.y + 3 + Math.sin(clock * 0.06) * 0.5, c.z + Math.sin(orbit) * 6);
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

	private void cast(int ticks) {
		entityData.set(CAST, ticks);
	}

	/** Метки шипов под каждым бойцом и рядом с ним (шип вырастает через {@link IceSpike#WARN} тиков). */
	private void spikes(ServerLevel level, List<ServerPlayer> fighters) {
		cast(16);
		playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 2.0F, 0.5F);
		int extra = phase() == 1 ? 1 : 2;
		for (ServerPlayer p : fighters) {
			if (prisons.stream().anyMatch(pr -> pr.player() == p)) {
				continue;  // узника тюрьмы шипы не трогают: его судьба — приговор
			}
			spawnSpike(level, p.getX(), p.getZ());
			for (int i = 0; i < extra; i++) {
				double a = random.nextDouble() * Math.PI * 2, r = 1.5 + random.nextDouble() * 2.5;
				spawnSpike(level, p.getX() + Math.cos(a) * r, p.getZ() + Math.sin(a) * r);
			}
		}
	}

	private void spawnSpike(ServerLevel level, double x, double z) {
		IceSpike spike = ModEntities.ICE_SPIKE.create(level, EntitySpawnReason.MOB_SUMMONED);
		if (spike == null) {
			return;
		}
		// на полу арены: от высоты дома вверх до первой опоры
		BlockPos at = BlockPos.containing(x, home.getY() + 1, z);
		for (int i = 0; i < 4 && !level.getBlockState(at.below()).isSolid(); i++) {
			at = at.below();
		}
		spike.snapTo(x, at.getY(), z, random.nextFloat() * 360, 0);
		spike.setup(this, phase() == 3 ? 11.0F : 9.0F);
		level.addFreshEntity(spike);
	}

	/** Залп ледяных осколков веером в цель. */
	private void volley(ServerLevel level, LivingEntity target) {
		cast(10);
		int count = phase() == 1 ? 3 : 5;
		Vec3 aim = target.getEyePosition().subtract(getEyePosition()).normalize();
		for (int i = 0; i < count; i++) {
			FrostShard shard = new FrostShard(ModEntities.FROST_SHARD, this, level);
			double spread = (i - (count - 1) / 2.0) * 0.12;
			Vec3 dir = aim.yRot((float) spread);
			shard.setPos(getX(), getEyeY() - 0.4, getZ());
			shard.shoot(dir.x, dir.y, dir.z, 1.1F, 1.5F);
			level.addFreshEntity(shard);
		}
		playSound(SoundEvents.SNOW_GOLEM_SHOOT, 2.0F, 0.6F);
	}

	/** Волна стужи: отбрасывает всех рядом, ранит и замедляет. */
	private void nova(ServerLevel level) {
		novaCooldown = 90;
		cast(12);
		for (int i = 0; i < 48; i++) {
			double a = i / 48.0 * Math.PI * 2;
			level.sendParticles(ParticleTypes.SNOWFLAKE, getX() + Math.cos(a) * 2, getY() + 0.5, getZ() + Math.sin(a) * 2, 1,
				Math.cos(a) * 0.6, 0.02, Math.sin(a) * 0.6, 0.6);
		}
		playSound(SoundEvents.PLAYER_HURT_FREEZE, 2.0F, 0.5F);
		for (ServerPlayer p : fighters(level)) {
			Vec3 to = p.position().subtract(position());
			if (to.length() < 5.0) {
				p.hurtServer(level, damageSources().mobAttack(this), 6.0F);
				Vec3 push = to.multiply(1, 0, 1).normalize().scale(1.4);
				p.push(push.x, 0.5, push.z);
				p.needsSync = true;
				p.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1));
			}
		}
	}

	/** Метель: снег вокруг бойцов, тепло тает быстрее; туман даёт полоса босса (createWorldFog). */
	private void blizzard(ServerLevel level, List<ServerPlayer> fighters) {
		if (clock % 4 == 0) {
			for (ServerPlayer p : fighters) {
				level.sendParticles(p, ParticleTypes.SNOWFLAKE, true, false, p.getX(), p.getY() + 2, p.getZ(), 30, 6, 3, 6, 0.15);
			}
		}
		if (clock % 20 == 0) {
			for (ServerPlayer p : fighters) {
				CelestialData.update(p, d -> d.withWarmth(d.warmth() - 2));
			}
		}
	}

	/** Рывок сквозь метель на другую сторону круга. */
	private void blink(ServerLevel level) {
		Vec3 from = position();
		orbit += Math.PI * (0.6 + random.nextDouble() * 0.8);
		Vec3 c = Vec3.atBottomCenterOf(home);
		Vec3 to = new Vec3(c.x + Math.cos(orbit) * 6, c.y + 3, c.z + Math.sin(orbit) * 6);
		for (int i = 0; i <= 12; i++) {
			Vec3 p = from.lerp(to, i / 12.0);
			level.sendParticles(ParticleTypes.SNOWFLAKE, p.x, p.y + 1.5, p.z, 6, 0.3, 0.8, 0.3, 0.02);
		}
		teleportTo(to.x, to.y, to.z);
		playSound(SoundEvents.ILLUSIONER_MIRROR_MOVE, 2.0F, 0.7F);
	}

	private void summon(ServerLevel level) {
		long alive = level.getEntitiesOfClass(Mob.class, getBoundingBox().inflate(ARENA), m -> m.entityTags().contains(SUMMON_TAG)).size();
		if (alive >= 5) {
			return;
		}
		cast(20);
		playSound(SoundEvents.EVOKER_PREPARE_SUMMON, 2.0F, 0.6F);
		for (int i = 0; i < 3; i++) {
			Mob mob = (i == 0 ? ModEntities.ICE_GUARDIAN : ModEntities.FROST_WRAITH).create(level, EntitySpawnReason.MOB_SUMMONED);
			if (mob == null) {
				continue;
			}
			double a = random.nextDouble() * Math.PI * 2;
			BlockPos at = BlockPos.containing(home.getX() + 0.5 + Math.cos(a) * 9, home.getY() + (i == 0 ? 0 : 3), home.getZ() + 0.5 + Math.sin(a) * 9);
			mob.snapTo(at, random.nextFloat() * 360, 0);
			mob.addTag(SUMMON_TAG);
			mob.addTag(dev.celestial.world.abyss.Darkness.NO_REPEL);
			level.addFreshEntity(mob);
			level.sendParticles(ParticleTypes.SNOWFLAKE, at.getX() + 0.5, at.getY() + 1, at.getZ() + 0.5, 40, 0.5, 1.0, 0.5, 0.05);
		}
	}

	/** Ледяная тюрьма: глыба вокруг игрока. Разбил хотя бы одну стенку у ног или у головы — вырвался. */
	private void imprison(ServerLevel level, List<ServerPlayer> fighters) {
		List<ServerPlayer> free = new ArrayList<>();
		for (ServerPlayer p : fighters) {
			if (prisons.stream().noneMatch(pr -> pr.player() == p)) {
				free.add(p);
			}
		}
		if (free.isEmpty()) {
			return;
		}
		ServerPlayer victim = free.get(random.nextInt(free.size()));
		cast(30);
		BlockPos c = victim.blockPosition();
		for (int i = 0; i < 6 && !level.getBlockState(c.below()).isSolid(); i++) {  // подброшенного шипом — вниз, на пол
			c = c.below();
		}
		victim.teleportTo(c.getX() + 0.5, c.getY(), c.getZ() + 0.5);
		victim.setDeltaMovement(Vec3.ZERO);
		victim.needsSync = true;
		List<BlockPos> blocks = new ArrayList<>();
		BlockState ice = ModBlocks.ARCHON_ICE.defaultBlockState();
		for (int dy = 0; dy <= 2; dy++) {
			for (int dx = -1; dx <= 1; dx++) {
				for (int dz = -1; dz <= 1; dz++) {
					boolean inside = dx == 0 && dz == 0 && dy < 2;
					boolean shell = Math.abs(dx) + Math.abs(dz) == 1 || dy == 2 && dx == 0 && dz == 0;
					BlockPos p = c.offset(dx, dy, dz);
					if (!inside && shell && level.getBlockState(p).isAir()) {
						level.setBlock(p, ice, 3);
						blocks.add(p.immutable());
					}
				}
			}
		}
		prisons.add(new Prison(victim, blocks, c, new int[] {PRISON_TIME}));
		level.playSound(null, c, SoundEvents.GLASS_PLACE, SoundSource.HOSTILE, 2.0F, 0.5F);
		victim.sendSystemMessage(Component.translatable("boss.celestial.frost_archon.prison"));
		victim.connection.send(new net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket(0, 30, 10));
		victim.connection.send(new net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket(Component.empty()));
		victim.connection.send(new net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket(
			Component.translatable("boss.celestial.frost_archon.prison_hint")));
	}

	private void tickPrisons(ServerLevel level) {
		prisons.removeIf(pr -> {
			pr.left()[0]--;
			boolean broken = pr.blocks().stream().anyMatch(p -> p.getY() < pr.center().getY() + 2 && !level.getBlockState(p).is(ModBlocks.ARCHON_ICE));
			Vec3 center = Vec3.atBottomCenterOf(pr.center());
			double dist = pr.player().position().distanceTo(center);
			boolean gone = !pr.player().isAlive() || pr.player().level() != level || dist > 3.0;  // умер или телепортировался прочь
			if (broken || gone) {
				shatter(level, pr);
				return true;
			}
			if (dist > 0.35) {  // узник не сдвигается с места ни отбросом, ни шагом — только разбить лёд
				pr.player().teleportTo(center.x, center.y, center.z);
			}
			pr.player().setDeltaMovement(Vec3.ZERO);
			pr.player().needsSync = true;
			if (pr.left()[0] % 10 == 0) {
				level.sendParticles(ParticleTypes.SNOWFLAKE, pr.center().getX() + 0.5, pr.center().getY() + 1, pr.center().getZ() + 0.5,
					10, 0.6, 0.8, 0.6, 0.02);
			}
			if (pr.left()[0] <= 0) {  // приговор: не вырвался — удар стужи
				cast(14);
				ServerPlayer p = pr.player();
				p.hurtServer(level, damageSources().indirectMagic(this, this), 12.0F);
				CelestialData.update(p, d -> d.withWarmth(d.warmth() - 30));
				p.setTicksFrozen(p.getTicksRequiredToFreeze() + 100);
				level.playSound(null, pr.center(), SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 2.5F, 0.4F);
				shatter(level, pr);
				return true;
			}
			return false;
		});
	}

	private void shatter(ServerLevel level, Prison pr) {
		for (BlockPos p : pr.blocks()) {
			if (level.getBlockState(p).is(ModBlocks.ARCHON_ICE)) {
				level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
				level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState()),
					p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 8, 0.3, 0.3, 0.3, 0.1);
			}
		}
	}

	private void onPhase(ServerLevel level, int phase) {
		playSound(SoundEvents.ENDER_DRAGON_GROWL, 3.0F, 1.4F);
		cast(30);
		bossEvent.setCreateWorldFog(phase >= 2);
		bossEvent.setColor(phase == 3 ? BossEvent.BossBarColor.WHITE : BossEvent.BossBarColor.BLUE);
		for (ServerPlayer p : bossEvent.getPlayers()) {
			p.sendSystemMessage(Component.translatable("boss.celestial.frost_archon.phase" + phase));
		}
		if (phase == 2) {
			summon(level);
		}
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (source.is(DamageTypeTags.IS_FREEZING) || source.is(DamageTypeTags.IS_FALL) || source.is(DamageTypeTags.IS_DROWNING)) {
			return false;
		}
		if (!(source.getEntity() instanceof Player) && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
			amount *= 0.1F;  // только руками героев: лава, кактусы и чужие мобы почти не ранят
		}
		return super.hurtServer(level, source, amount);
	}

	@Override
	public void die(DamageSource source) {
		super.die(source);
		if (level() instanceof ServerLevel level) {
			for (Prison pr : prisons) {
				shatter(level, pr);
			}
			prisons.clear();
			for (Mob m : level.getEntitiesOfClass(Mob.class, getBoundingBox().inflate(ARENA + 8), m -> m.entityTags().contains(SUMMON_TAG))) {
				level.sendParticles(ParticleTypes.SNOWFLAKE, m.getX(), m.getY(0.5), m.getZ(), 20, 0.4, 0.6, 0.4, 0.05);
				m.discard();
			}
			level.sendParticles(ParticleTypes.END_ROD, getX(), getY(0.5), getZ(), 300, 3, 3, 3, 0.4);
			level.sendParticles(ParticleTypes.SNOWFLAKE, getX(), getY(0.5), getZ(), 400, 6, 4, 6, 0.3);
			dev.celestial.story.StoryEvents.onArchonDefeated(level, this, home);
		}
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (level().isClientSide()) {
			if (random.nextInt(2) == 0) {
				level().addParticle(ParticleTypes.SNOWFLAKE, getRandomX(1.2), getRandomY(), getRandomZ(1.2), 0, -0.04, 0);
			}
			if (casting() > 0) {
				level().addParticle(ParticleTypes.END_ROD, getX(), getY() + 3.6, getZ(), (random.nextDouble() - 0.5) * 0.2, 0.05,
					(random.nextDouble() - 0.5) * 0.2);
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
	public boolean canFreeze() {
		return false;
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
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		home = input.read("Home", BlockPos.CODEC).orElse(BlockPos.ZERO);
		int phase = input.getIntOr("Phase", 1);
		entityData.set(PHASE, phase);
		bossEvent.setCreateWorldFog(phase >= 2);
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return SoundEvents.AMETHYST_BLOCK_CHIME;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.GLASS_HIT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.ENDER_DRAGON_DEATH;
	}

	@Override
	public float getVoicePitch() {
		return 0.5F;
	}
}
