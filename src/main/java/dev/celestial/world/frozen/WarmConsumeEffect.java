package dev.celestial.world.frozen;

import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import dev.celestial.Celestial;
import dev.celestial.data.CelestialData;
import dev.celestial.registry.ModEffects;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.item.v1.DefaultItemComponentEvents;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.Consumable;
import net.minecraft.world.item.consume_effects.ConsumeEffect;
import net.minecraft.world.level.Level;

/**
 * Горячая еда: поднимает тепло и даёт «Согрев» (тепло не тает) на seconds секунд. Тип эффекта поедания `celestial:warm` —
 * data-driven, без миксинов: вешается и на свои блюда, и (через DefaultItemComponentEvents) на ванильные супы и рагу.
 */
public record WarmConsumeEffect(float warmth, int seconds) implements ConsumeEffect {
	public static final MapCodec<WarmConsumeEffect> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
		com.mojang.serialization.Codec.FLOAT.fieldOf("warmth").forGetter(WarmConsumeEffect::warmth),
		com.mojang.serialization.Codec.INT.optionalFieldOf("seconds", 60).forGetter(WarmConsumeEffect::seconds)
	).apply(i, WarmConsumeEffect::new));
	public static final StreamCodec<RegistryFriendlyByteBuf, WarmConsumeEffect> STREAM_CODEC = StreamCodec.composite(
		ByteBufCodecs.FLOAT, WarmConsumeEffect::warmth, ByteBufCodecs.VAR_INT, WarmConsumeEffect::seconds, WarmConsumeEffect::new);
	public static final ConsumeEffect.Type<WarmConsumeEffect> TYPE = Registry.register(BuiltInRegistries.CONSUME_EFFECT_TYPE,
		Celestial.id("warm"), new ConsumeEffect.Type<>(CODEC, STREAM_CODEC));

	@Override
	public ConsumeEffect.Type<WarmConsumeEffect> getType() {
		return TYPE;
	}

	@Override
	public boolean apply(Level level, ItemStack stack, LivingEntity user) {
		if (user instanceof ServerPlayer player) {
			CelestialData.update(player, d -> d.withWarmth(Math.min(100.0F, d.warmth() + warmth)));
			player.addEffect(new MobEffectInstance(ModEffects.WARMED, seconds * 20, 0, false, true, true));
			ServerLevel server = (ServerLevel) level;
			for (ServerPlayer other : server.players()) {  // пар от горячего видят окружающие; самому едоку он закрывал бы экран
				if (other != player && other.distanceToSqr(player) < 32 * 32) {
					server.sendParticles(other, ParticleTypes.WHITE_SMOKE, false, false, player.getX(), player.getEyeY() + 0.2, player.getZ(), 4, 0.2, 0.1, 0.2, 0.01);
				}
			}
		}
		return true;
	}

	/** Ванильные горячие блюда тоже греют. */
	public static void init() {
		DefaultItemComponentEvents.MODIFY.register(context -> {
			warm(context, Items.MUSHROOM_STEW, 30, 45);
			warm(context, Items.BEETROOT_SOUP, 30, 45);
			warm(context, Items.RABBIT_STEW, 45, 75);
			warm(context, Items.SUSPICIOUS_STEW, 25, 30);
		});
	}

	private static void warm(DefaultItemComponentEvents.ModifyContext context, Item item, float warmth, int seconds) {
		context.modify(item, (builder, registries, it) -> {
			Consumable base = it.components().get(DataComponents.CONSUMABLE);
			if (base == null) {
				return;
			}
			List<ConsumeEffect> effects = new ArrayList<>(base.onConsumeEffects());
			effects.add(new WarmConsumeEffect(warmth, seconds));
			builder.set(DataComponents.CONSUMABLE, new Consumable(base.consumeSeconds(), base.animation(), base.sound(), base.hasConsumeParticles(), effects));
		});
	}
}
