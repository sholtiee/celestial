package dev.celestial.entity;

import dev.celestial.astral.StarDiskBlock;
import dev.celestial.astral.StarSocketBlock;
import dev.celestial.data.CelestialData;
import dev.celestial.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * Пожиратель звёзд — угорь пустоты с пастью-воронкой. Кусает и выпивает Сияние (−20) с краткой Тьмой. Без цели — ищет
 * незажжённый Звёздный диск рядом и выдёргивает из гнезда вставленный камень: собирая созвездие, береги святилище.
 * Свет его отпугивает: у гнёзд с блочным светом ≥ 12 (фонари, огни святилища) камни не трогает.
 */
public class StarDevourer extends Mob implements Enemy {
	private static final byte EVENT_BITE = 4;
	private int biteCooldown;
	private int biteAnim;
	private BlockPos prey;

	public StarDevourer(EntityType<? extends StarDevourer> type, Level level) {
		super(type, level);
		this.moveControl = new FlyingMoveControl<>(this, 15, true);
		this.xpReward = 14;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes()
			.add(Attributes.MAX_HEALTH, 30.0)
			.add(Attributes.ARMOR, 2.0)
			.add(Attributes.FLYING_SPEED, 0.45)
			.add(Attributes.MOVEMENT_SPEED, 0.25)
			.add(Attributes.ATTACK_DAMAGE, 6.0)
			.add(Attributes.FOLLOW_RANGE, 24.0);
	}

	@Override
	protected PathNavigation createNavigation(Level level) {
		FlyingPathNavigation nav = new FlyingPathNavigation(this, level);
		nav.setCanFloat(true);
		return nav;
	}

	@Override
	public void travel(Vec3 input) {
		travelFlying(input, getSpeed());
	}

	public float biteProgress(float partial) {
		return biteAnim > 0 ? (biteAnim - partial) / 10.0F : 0.0F;
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (biteCooldown > 0) {
			biteCooldown--;
		}
		ServerPlayer target = (ServerPlayer) level.getNearestPlayer(getX(), getY(), getZ(), 24,
			p -> p instanceof ServerPlayer sp && !sp.isCreative() && !sp.isSpectator());
		if (target != null) {
			prey = null;
			getNavigation().moveTo(target.getX(), target.getEyeY() - 0.4, target.getZ(), 1.2);
			getLookControl().setLookAt(target);
			if (biteCooldown == 0 && distanceToSqr(target) < 4.0) {
				biteCooldown = 30;
				biteAnim = 10;
				level.broadcastEntityEvent(this, EVENT_BITE);
				if (target.hurtServer(level, damageSources().mobAttack(this), (float) getAttributeValue(Attributes.ATTACK_DAMAGE))) {
					CelestialData.update(target, d -> d.withRadiance(Math.max(0, d.radiance() - 20)));
					target.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 60, 0), this);
					level.sendParticles(ParticleTypes.SCULK_SOUL, target.getX(), target.getEyeY(), target.getZ(), 8, 0.3, 0.3, 0.3, 0.02);
				}
			}
			return;
		}
		if (tickCount % 100 == getId() % 100) {
			prey = findPrey(level);
		}
		if (prey != null) {
			getNavigation().moveTo(prey.getX() + 0.5, prey.getY() + 1.5, prey.getZ() + 0.5, 0.9);
			if (blockPosition().closerThan(prey, 2.5)) {
				BlockState s = level.getBlockState(prey);
				if (s.is(ModBlocks.STAR_SOCKET) && s.getValue(StarSocketBlock.FILLED)) {
					level.setBlock(prey, s.setValue(StarSocketBlock.FILLED, false), Block.UPDATE_ALL);
					level.addFreshEntity(new ItemEntity(level, prey.getX() + 0.5, prey.getY() + 1.2, prey.getZ() + 0.5,
						new ItemStack(dev.celestial.registry.ModItems.STAR_STONE)));
					level.playSound(null, prey, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.HOSTILE, 1.0F, 0.6F);
					level.sendParticles(ParticleTypes.SCULK_SOUL, prey.getX() + 0.5, prey.getY() + 1, prey.getZ() + 0.5, 12, 0.3, 0.3, 0.3, 0.02);
				}
				prey = null;
			}
		} else if (getNavigation().isDone() && random.nextInt(40) == 0) {
			Vec3 p = position().add((random.nextDouble() - 0.5) * 24, (random.nextDouble() - 0.5) * 8, (random.nextDouble() - 0.5) * 24);
			getNavigation().moveTo(p.x, p.y, p.z, 0.7);
		}
	}

	/** Вставленный камень в гнезде у незажжённого диска в радиусе 16, где темно (свет отпугивает). */
	private BlockPos findPrey(ServerLevel level) {
		BlockPos at = blockPosition();
		for (BlockPos p : BlockPos.betweenClosed(at.offset(-16, -8, -16), at.offset(16, 8, 16))) {
			BlockState s = level.getBlockState(p);
			if (s.is(ModBlocks.STAR_DISK) && !s.getValue(StarDiskBlock.LIT)) {
				for (BlockPos q : BlockPos.betweenClosed(p.offset(-2, 0, -2), p.offset(2, 0, 2))) {
					BlockState qs = level.getBlockState(q);
					if (qs.is(ModBlocks.STAR_SOCKET) && qs.getValue(StarSocketBlock.FILLED)
						&& level.getBrightness(net.minecraft.world.level.LightLayer.BLOCK, q.above()) < 12) {  // свет фонарей/огней, не звёздное небо
						return q.immutable();
					}
				}
			}
		}
		return null;
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (biteAnim > 0) {
			biteAnim--;
		}
		if (level().isClientSide() && random.nextInt(3) == 0) {
			level().addParticle(ParticleTypes.REVERSE_PORTAL, getRandomX(0.6), getRandomY(), getRandomZ(0.6), 0, 0, 0);
		}
	}

	@Override
	public void handleEntityEvent(byte id) {
		if (id == EVENT_BITE) {
			biteAnim = 10;
		} else {
			super.handleEntityEvent(id);
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
		return SoundEvents.WARDEN_AMBIENT;
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
		return 0.6F;
	}
}
