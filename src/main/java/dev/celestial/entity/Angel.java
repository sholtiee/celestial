package dev.celestial.entity;

import dev.celestial.Celestial;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import dev.celestial.registry.ModItems;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.npc.wanderingtrader.WanderingTrader;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.item.trading.TradeSet;
import net.minecraft.world.level.Level;

/** Небесный житель: торгует дарами Рая за эфирит и звёздный кварц. Никуда не уходит. */
public class Angel extends WanderingTrader {
	public static final ResourceKey<TradeSet> COMMON = ResourceKey.create(Registries.TRADE_SET, Celestial.id("angel/common"));
	public static final ResourceKey<TradeSet> RARE = ResourceKey.create(Registries.TRADE_SET, Celestial.id("angel/rare"));
	/** Профессия: 0 — хранитель, 1 — кузнец, 2 — звездочёт, 3 — садовник. */
	public static final String[] PROFESSIONS = {"keeper", "smith", "astronomer", "gardener"};
	private static final net.minecraft.network.syncher.EntityDataAccessor<Integer> PROFESSION =
		net.minecraft.network.syncher.SynchedEntityData.defineId(Angel.class, net.minecraft.network.syncher.EntityDataSerializers.INT);

	public Angel(EntityType<? extends Angel> type, Level level) {
		super(type, level);
		this.setItemSlot(EquipmentSlot.CHEST, new ItemStack(ModItems.SERAPH_WINGS));
		this.setDropChance(EquipmentSlot.CHEST, 0.0F);
	}

	/** Как у странствующего торговца, но без зелья невидимости по ночам: Рай живёт по часам Верхнего мира, и ангелы пропадали каждую ночь. */
	@Override
	protected void registerGoals() {
		goalSelector.addGoal(0, new net.minecraft.world.entity.ai.goal.FloatGoal(this));
		goalSelector.addGoal(1, new net.minecraft.world.entity.ai.goal.TradeWithPlayerGoal(this));
		goalSelector.addGoal(1, new net.minecraft.world.entity.ai.goal.AvoidEntityGoal<>(this, net.minecraft.world.entity.monster.zombie.Zombie.class, 8.0F, 0.5, 0.5));
		goalSelector.addGoal(1, new net.minecraft.world.entity.ai.goal.AvoidEntityGoal<>(this, dev.celestial.entity.FallenGuardian.class, 10.0F, 0.5, 0.5));
		goalSelector.addGoal(1, new net.minecraft.world.entity.ai.goal.PanicGoal(this, 0.5));
		goalSelector.addGoal(1, new net.minecraft.world.entity.ai.goal.LookAtTradingPlayerGoal(this));
		goalSelector.addGoal(4, new net.minecraft.world.entity.ai.goal.MoveTowardsRestrictionGoal(this, 0.35));
		goalSelector.addGoal(8, new net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal(this, 0.35));
		goalSelector.addGoal(9, new net.minecraft.world.entity.ai.goal.InteractGoal(this, net.minecraft.world.entity.player.Player.class, 3.0F, 1.0F));
		goalSelector.addGoal(10, new net.minecraft.world.entity.ai.goal.LookAtPlayerGoal(this, Mob.class, 8.0F));
	}

	/** Ангелы постоянные, а у WanderingTrader нет пополнения сделок: раз в игровые сутки сделки восстанавливаются. */
	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		long day = level.getOverworldClockTime() / 24000L;
		if (day != restockDay && !isTrading()) {
			restockDay = day;
			for (var offer : getOffers()) {
				offer.resetUses();
			}
		}
	}

	private long restockDay = -1;

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes()
			.add(Attributes.MAX_HEALTH, 30.0)
			.add(Attributes.MOVEMENT_SPEED, 0.45)
			.add(Attributes.SAFE_FALL_DISTANCE, 64.0);
	}

	@Override
	protected void defineSynchedData(net.minecraft.network.syncher.SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(PROFESSION, -1);
	}

	public int getProfession() {
		int p = entityData.get(PROFESSION);
		if (p < 0 && !level().isClientSide()) {
			p = random.nextInt(PROFESSIONS.length);
			entityData.set(PROFESSION, p);
		}
		return Math.max(0, p);
	}

	@Override
	protected void addAdditionalSaveData(net.minecraft.world.level.storage.ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putInt("Profession", getProfession());
	}

	@Override
	protected void readAdditionalSaveData(net.minecraft.world.level.storage.ValueInput input) {
		super.readAdditionalSaveData(input);
		entityData.set(PROFESSION, input.getIntOr("Profession", -1));
	}

	@Override
	protected void updateTrades(ServerLevel level) {
		MerchantOffers offers = this.getOffers();
		this.addOffersFromTradeSet(level, offers, COMMON);
		this.addOffersFromTradeSet(level, offers, ResourceKey.create(Registries.TRADE_SET, Celestial.id("angel/" + PROFESSIONS[getProfession()])));
		this.addOffersFromTradeSet(level, offers, RARE);
	}

	/** Скидка за репутацию у ангелов: −1 к цене за каждые 25 очков (но не меньше 1). */
	@Override
	public void setTradingPlayer(net.minecraft.world.entity.player.@org.jspecify.annotations.Nullable Player player) {
		if (player != null && !level().isClientSide()) {
			int discount = dev.celestial.data.CelestialData.get(player).reputation() / 25;
			for (var offer : getOffers()) {
				offer.setSpecialPriceDiff(-Math.min(discount, offer.getBaseCostA().getCount() - 1));
			}
		} else if (player == null && !level().isClientSide()) {
			for (var offer : getOffers()) {
				offer.resetSpecialPriceDiff();
			}
		}
		super.setTradingPlayer(player);
	}

	/** Изгнанные (плод Познания) для ангелов — чужие: торговли нет, пока не снято «Изгнание». */
	@Override
	public net.minecraft.world.InteractionResult mobInteract(net.minecraft.world.entity.player.Player player, net.minecraft.world.InteractionHand hand) {
		if (dev.celestial.eden.Exile.isExiled(player)) {
			if (!level().isClientSide()) {
				player.sendOverlayMessage(net.minecraft.network.chat.Component.translatable("eden.celestial.cold"));
			}
			return net.minecraft.world.InteractionResult.CONSUME;
		}
		return super.mobInteract(player, hand);
	}

	@Override
	public boolean removeWhenFarAway(double distSqr) {
		return false;
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return isTrading() ? SoundEvents.ALLAY_AMBIENT_WITH_ITEM : SoundEvents.ALLAY_AMBIENT_WITHOUT_ITEM;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.ALLAY_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.ALLAY_DEATH;
	}

	@Override
	public float getVoicePitch() {
		return 0.8F;
	}
}
