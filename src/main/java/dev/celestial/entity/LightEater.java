package dev.celestial.entity;

import dev.celestial.data.CelestialData;
import dev.celestial.registry.ModSounds;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.TagKey;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Светоед — крылатая «моль» Бездны. Летит на свет: съедает факелы и фонари поблизости (с каждым светится ярче),
 * к игроку с огнём в руке подлетает вплотную, высасывает Сияние и кусает. Хрупкий — 12 здоровья.
 */
public class LightEater extends Mob implements Enemy {
	public static final TagKey<net.minecraft.world.level.block.Block> EDIBLE = TagKey.create(Registries.BLOCK, dev.celestial.Celestial.id("edible_lights"));
	private static final EntityDataAccessor<Integer> FULLNESS = SynchedEntityData.defineId(LightEater.class, EntityDataSerializers.INT);
	private @Nullable BlockPos meal;
	private int searchCooldown;
	private int biteCooldown;

	public LightEater(EntityType<? extends LightEater> type, Level level) {
		super(type, level);
		this.moveControl = new FlyingMoveControl<>(this, 20, true);
		this.xpReward = 6;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes()
			.add(Attributes.MAX_HEALTH, 12.0)
			.add(Attributes.FLYING_SPEED, 0.6)
			.add(Attributes.MOVEMENT_SPEED, 0.3)
			.add(Attributes.ATTACK_DAMAGE, 2.0)
			.add(Attributes.FOLLOW_RANGE, 24.0);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(FULLNESS, 0);
	}

	/** Сколько света съедено (0–5): брюшко светится ярче. */
	public int fullness() {
		return entityData.get(FULLNESS);
	}

	@Override
	protected PathNavigation createNavigation(Level level) {
		FlyingPathNavigation nav = new FlyingPathNavigation(this, level);
		nav.setCanOpenDoors(false);
		nav.setCanFloat(true);
		return nav;
	}

	@Override
	public void travel(Vec3 input) {
		travelFlying(input, getSpeed());
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (biteCooldown > 0) {
			biteCooldown--;
		}
		ServerPlayer lightBearer = (ServerPlayer) level.getNearestPlayer(getX(), getY(), getZ(), 12.0,
			p -> p instanceof ServerPlayer sp && !sp.isCreative() && !sp.isSpectator() && dev.celestial.world.abyss.Darkness.holdsLight(sp));
		if (lightBearer != null) {
			huntPlayer(level, lightBearer);
			return;
		}
		if (meal != null && !level.getBlockState(meal).is(EDIBLE)) {
			meal = null;
		}
		if (meal == null && --searchCooldown <= 0) {
			searchCooldown = 40;
			meal = findLight(level);
		}
		if (meal != null) {
			getNavigation().moveTo(meal.getX() + 0.5, meal.getY() + 0.5, meal.getZ() + 0.5, 1.0);
			if (distanceToSqr(Vec3.atCenterOf(meal)) < 2.5) {
				eat(level, meal);
				meal = null;
			}
		} else if (getNavigation().isDone() && random.nextInt(40) == 0) {
			Vec3 p = position().add((random.nextDouble() - 0.5) * 16, (random.nextDouble() - 0.4) * 6, (random.nextDouble() - 0.5) * 16);
			getNavigation().moveTo(p.x, p.y, p.z, 0.7);
		}
	}

	private void huntPlayer(ServerLevel level, ServerPlayer player) {
		getNavigation().moveTo(player.getX(), player.getEyeY(), player.getZ(), 1.3);
		getLookControl().setLookAt(player);
		if (distanceToSqr(player) < 4 && biteCooldown == 0) {
			biteCooldown = 20;
			CelestialData.update(player, d -> d.withRadiance(d.radiance() - 5));
			player.hurtServer(level, damageSources().mobAttack(this), (float) getAttributeValue(Attributes.ATTACK_DAMAGE));
			level.sendParticles(ParticleTypes.END_ROD, player.getX(), player.getEyeY(), player.getZ(), 6, 0.3, 0.3, 0.3, 0.02);
			playSound(ModSounds.LIGHT_EATER_FEED, 0.8F, 1.3F);
		}
	}

	private @Nullable BlockPos findLight(ServerLevel level) {
		BlockPos center = blockPosition();
		BlockPos best = null;
		for (BlockPos p : BlockPos.betweenClosed(center.offset(-12, -6, -12), center.offset(12, 6, 12))) {
			if (level.getBlockState(p).is(EDIBLE) && (best == null || p.distSqr(center) < best.distSqr(center))) {
				best = p.immutable();
			}
		}
		return best;
	}

	/** Съедает источник света: блок исчезает (без выпадения), Светоед лечится и светится ярче. */
	private void eat(ServerLevel level, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		level.levelEvent(2001, pos, Block.getId(state));
		level.removeBlock(pos, false);
		heal(4.0F);
		entityData.set(FULLNESS, Math.min(5, fullness() + 1));
		level.sendParticles(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 15, 0.2, 0.2, 0.2, 0.05);
		level.playSound(null, pos, ModSounds.LIGHT_EATER_FEED, SoundSource.HOSTILE, 1.0F, 1.0F);
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (level().isClientSide() && random.nextInt(6 - Math.min(5, fullness())) == 0) {
			level().addParticle(dev.celestial.registry.ModParticles.STARLIGHT, getRandomX(0.4), getRandomY(), getRandomZ(0.4), 0, -0.02, 0);
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
	protected SoundEvent getAmbientSound() {
		return SoundEvents.BEE_LOOP;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.PHANTOM_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.PHANTOM_DEATH;
	}

	@Override
	public float getVoicePitch() {
		return 1.6F;
	}
}
