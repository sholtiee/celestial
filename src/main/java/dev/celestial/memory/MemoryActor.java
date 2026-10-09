package dev.celestial.memory;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.Level;

/**
 * Актёр воспоминания (docs/LORE.md §5b–5c): фигура из памяти — Адам, Ева, Змей и другие. Своего ИИ нет: им управляет сцена
 * ({@link Memories}), двигая по таймлайну. Облик — `skin` (текстура `memory_<skin>`), поза — `scenePose` (0 стоит, 1 протягивает руку,
 * 2 подносит ко рту, 3 пригнулся, 4 на коленях). Неуязвим, не сохраняется в мире: сцена создаёт актёров заново при каждом входе.
 */
public class MemoryActor extends PathfinderMob {
	private static final EntityDataAccessor<String> SKIN = SynchedEntityData.defineId(MemoryActor.class, EntityDataSerializers.STRING);
	private static final EntityDataAccessor<Integer> POSE_ID = SynchedEntityData.defineId(MemoryActor.class, EntityDataSerializers.INT);

	public static final int STAND = 0;
	public static final int OFFER = 1;
	public static final int EAT = 2;
	public static final int CROUCH = 3;
	public static final int KNEEL = 4;

	public MemoryActor(EntityType<? extends MemoryActor> type, Level level) {
		super(type, level);
		setNoGravity(true);
		setNoAi(true);
		setSilent(true);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return PathfinderMob.createMobAttributes().add(Attributes.MAX_HEALTH, 20.0).add(Attributes.MOVEMENT_SPEED, 0.2);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(SKIN, "");
		builder.define(POSE_ID, STAND);
	}

	public String skin() {
		return entityData.get(SKIN);
	}

	public void setSkin(String skin) {
		entityData.set(SKIN, skin);
	}

	public int scenePose() {
		return entityData.get(POSE_ID);
	}

	public void setScenePose(int pose) {
		entityData.set(POSE_ID, pose);
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (level().isClientSide() && random.nextInt(6) == 0) {  // пылинки света: видно, что это память
			level().addParticle(ParticleTypes.END_ROD, getRandomX(0.6), getRandomY(), getRandomZ(0.6), 0, 0.01, 0);
		}
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		return source.is(DamageTypeTags.BYPASSES_INVULNERABILITY) && super.hurtServer(level, source, amount);
	}

	@Override
	public boolean isPushable() {
		return false;
	}

	@Override
	public boolean removeWhenFarAway(double distSqr) {
		return false;
	}

	@Override
	public boolean shouldBeSaved() {
		return false;
	}
}
