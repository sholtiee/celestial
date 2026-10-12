package dev.celestial.entity;

import dev.celestial.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.RandomSource;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.animal.equine.AbstractHorse;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Заводной конь — ездовой автомат мастеров. Дикие стоят на Медных равнинах с кончившимся заводом. Не ест и не приручается
 * лаской: его заводят <b>Заводным ключом</b> (ПКМ) — конь становится твоим и получает 5 минут хода (до 10 копится).
 * Пока завод есть — бежит быстро и прыгает высоко, из трубы идёт пар; кончился — плетётся вчетверо медленнее.
 * Чинится медными и хронитовыми слитками, не горит, не плавает (тонет — тяжёлый).
 */
public class ClockworkHorse extends AbstractHorse {
	private static final EntityDataAccessor<Integer> WIND = SynchedEntityData.defineId(ClockworkHorse.class, EntityDataSerializers.INT);
	public static final int WIND_PER_KEY = 6000;
	public static final int WIND_MAX = 12000;

	public ClockworkHorse(EntityType<? extends ClockworkHorse> type, Level level) {
		super(type, level);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return createBaseHorseAttributes()
			.add(Attributes.MAX_HEALTH, 40.0)
			.add(Attributes.ARMOR, 6.0)
			.add(Attributes.MOVEMENT_SPEED, 0.34)
			.add(Attributes.JUMP_STRENGTH, 0.95)
			.add(Attributes.SAFE_FALL_DISTANCE, 10.0)
			.add(Attributes.STEP_HEIGHT, 1.5);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(WIND, 0);
	}

	@Override
	protected void registerGoals() {
		// без «бешеного бега» и размножения: это машина
		goalSelector.addGoal(0, new FloatGoal(this));
		goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.6) {
			@Override
			public boolean canUse() {
				return wind() > 0 && super.canUse();
			}
		});
		goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 6.0F));
		goalSelector.addGoal(8, new RandomLookAroundGoal(this));
	}

	public int wind() {
		return entityData.get(WIND);
	}

	@Override
	public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
		@Nullable SpawnGroupData data) {
		RandomSource r = level.getRandom();
		if (reason != EntitySpawnReason.SPAWN_ITEM_USE && r.nextInt(3) == 0) {
			entityData.set(WIND, 200 + r.nextInt(800));  // кое-кто из диких ещё не встал
		}
		return super.finalizeSpawn(level, difficulty, reason, data);
	}

	@Override
	public InteractionResult mobInteract(Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		if (stack.is(ModItems.WIND_KEY) && !isVehicle()) {
			if (level() instanceof ServerLevel) {
				if (!isTamed()) {
					tameWithName(player);
				}
				entityData.set(WIND, Math.min(WIND_MAX, wind() + WIND_PER_KEY));
				stack.hurtAndBreak(1, player, hand.asEquipmentSlot());
				playSound(dev.celestial.registry.ModSounds.SENTRY_WIND, 1.0F, 0.8F);
				player.sendOverlayMessage(Component.translatable("entity.celestial.clockwork_horse.wound", wind() / 1200));
			}
			return InteractionResult.SUCCESS;
		}
		if (!isTamed() && !isVehicle() && !isBaby()) {
			if (level() instanceof ServerLevel) {
				player.sendOverlayMessage(Component.translatable("entity.celestial.clockwork_horse.need_key"));
			}
			return InteractionResult.SUCCESS;
		}
		return super.mobInteract(player, hand);
	}

	@Override
	public boolean isFood(ItemStack stack) {
		return stack.is(Items.COPPER_INGOT) || stack.is(ModItems.CHRONITE_INGOT);
	}

	@Override
	protected boolean handleEating(Player player, ItemStack stack) {
		if (!isFood(stack) || getHealth() >= getMaxHealth()) {
			return false;
		}
		heal(stack.is(ModItems.CHRONITE_INGOT) ? 20.0F : 6.0F);
		playSound(SoundEvents.ANVIL_USE, 0.5F, 1.6F);
		return true;
	}

	@Override
	public boolean canMate(net.minecraft.world.entity.animal.Animal partner) {
		return false;
	}

	@Override
	public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
		return null;
	}

	@Override
	protected float getRiddenSpeed(Player controller) {
		float base = super.getRiddenSpeed(controller);
		return wind() > 0 ? base : base * 0.25F;
	}

	@Override
	public boolean canJump() {
		return super.canJump() && wind() > 0;
	}

	@Override
	protected void tickRidden(Player controller, Vec3 riddenInput) {
		super.tickRidden(controller, riddenInput);
		if (!level().isClientSide() && wind() > 0 && riddenInput.lengthSqr() > 0) {
			entityData.set(WIND, wind() - 1);
			if (wind() == 0) {
				playSound(SoundEvents.IRON_GOLEM_DAMAGE, 0.8F, 1.4F);
				controller.sendOverlayMessage(Component.translatable("entity.celestial.clockwork_horse.unwound"));
			}
		}
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (level().isClientSide() && wind() > 0 && random.nextInt(isVehicle() ? 2 : 6) == 0) {
			// пар из трубы на спине
			double yaw = Math.toRadians(yBodyRot);
			double bx = getX() + Math.sin(yaw) * 0.45, bz = getZ() - Math.cos(yaw) * 0.45;
			level().addParticle(ParticleTypes.WHITE_SMOKE, bx, getY() + 1.75, bz, 0, 0.05, 0);
		}
	}

	@Override
	public boolean isImmobile() {
		return super.isImmobile() || (wind() == 0 && !isVehicle());
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putInt("Wind", wind());
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		entityData.set(WIND, input.getIntOr("Wind", 0));
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return wind() > 0 ? dev.celestial.registry.ModSounds.HORSE_WHINNY : null;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.IRON_GOLEM_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.IRON_GOLEM_DEATH;
	}

	@Override
	protected @Nullable SoundEvent getAngrySound() {
		return dev.celestial.registry.ModSounds.HORSE_WHINNY;
	}

	@Override
	protected void playStepSound(BlockPos pos, BlockState state) {
		playSound(SoundEvents.NETHERITE_BLOCK_STEP, 0.6F, 1.2F);
	}

	@Override
	public float getVoicePitch() {
		return 1.2F;
	}
}
