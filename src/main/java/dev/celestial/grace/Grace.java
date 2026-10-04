package dev.celestial.grace;

import dev.celestial.Celestial;
import dev.celestial.data.CelestialData;
import dev.celestial.data.PlayerData;
import dev.celestial.world.HeavenDimension;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;

/** Благодать на сервере: изучение навыков, пассивные бонусы, восстановление Сияния, «Второе дыхание». */
public final class Grace {
	private static final Map<UUID, Long> SECOND_WIND_USED = new ConcurrentHashMap<>();
	private static final long SECOND_WIND_COOLDOWN = 20 * 60 * 10;

	/** Состояние привязано ко времени мира: между мирами одиночной игры его надо сбрасывать (иначе «Второе дыхание» не работало в новом мире). */
	public static void clearState() {
		SECOND_WIND_USED.clear();
	}

	private Grace() {}

	public static void init() {
		PayloadTypeRegistry.serverboundPlay().register(GracePayloads.LearnSkill.TYPE, GracePayloads.LearnSkill.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(GracePayloads.CastSpell.TYPE, GracePayloads.CastSpell.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(GracePayloads.LearnSkill.TYPE, (payload, ctx) -> learn(ctx.player(), payload.skill()));
		ServerPlayNetworking.registerGlobalReceiver(GracePayloads.CastSpell.TYPE, (payload, ctx) -> Spells.cast(ctx.player(), payload.spell()));
		ServerTickEvents.END_SERVER_TICK.register(Grace::tick);
		ServerLivingEntityEvents.ALLOW_DEATH.register((entity, source, amount) -> {
			if (!(entity instanceof ServerPlayer player) || !CelestialData.get(player).hasSkill(Skill.SECOND_WIND.id)) {
				return true;
			}
			long now = player.level().getGameTime();
			Long last = SECOND_WIND_USED.get(player.getUUID());
			if (last != null && now - last < SECOND_WIND_COOLDOWN) {
				return true;
			}
			SECOND_WIND_USED.put(player.getUUID(), now);
			player.setHealth(8.0F);
			player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 100, 3));
			player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 200, 1));
			player.level().sendParticles(ParticleTypes.TOTEM_OF_UNDYING, player.getX(), player.getY(1.0), player.getZ(), 60, 0.5, 1, 0.5, 0.3);
			player.level().playSound(null, player.blockPosition(), SoundEvents.TOTEM_USE, SoundSource.PLAYERS, 1.0F, 1.4F);
			player.sendSystemMessage(Component.translatable("grace.celestial.second_wind"));
			return false;
		});
	}

	public static boolean learn(ServerPlayer player, String id) {
		Skill skill = Skill.byId(id);
		PlayerData data = CelestialData.get(player);
		if (skill == null || data.hasSkill(id)) {
			return false;
		}
		if (skill.requires != null && !data.hasSkill(skill.requires.id)) {
			player.sendOverlayMessage(Component.translatable("grace.celestial.locked"));
			return false;
		}
		if (data.grace() < skill.cost) {
			player.sendOverlayMessage(Component.translatable("grace.celestial.not_enough", skill.cost));
			return false;
		}
		CelestialData.update(player, d -> d.withGrace(d.grace() - skill.cost).withSkill(id));
		player.level().playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.0F, 1.2F);
		player.sendOverlayMessage(Component.translatable("grace.celestial.learned", Component.translatable("skill.celestial." + id)));
		applyPassives(player, CelestialData.get(player));
		return true;
	}

	public static float maxRadiance(PlayerData data) {
		return data.hasSkill(Skill.RADIANCE_POOL.id) ? 150.0F : 100.0F;
	}

	private static void tick(MinecraftServer server) {
		if (server.getTickCount() % 20 != 0) {
			return;
		}
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			PlayerData data = CelestialData.get(player);
			float max = maxRadiance(data);
			float regen = (data.hasSkill(Skill.RADIANCE_REGEN.id) ? 2.0F : 1.0F) * (HeavenDimension.isHeaven(player.level()) ? 2.0F : 1.0F);
			if (data.radiance() < max) {
				CelestialData.update(player, d -> d.withRadiance(Math.min(max, d.radiance() + regen)));
			}
			applyPassives(player, data);
		}
	}

	/** Пассивные бонусы навыков (модификаторы атрибутов ставятся/снимаются по наличию навыка). */
	public static void applyPassives(ServerPlayer player, PlayerData data) {
		toggle(player.getAttribute(Attributes.MAX_HEALTH), "skill_vigor", 4.0, AttributeModifier.Operation.ADD_VALUE, data.hasSkill(Skill.VIGOR.id));
		toggle(player.getAttribute(Attributes.ATTACK_DAMAGE), "skill_heavenly_strike", 0.15, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL,
			data.hasSkill(Skill.HEAVENLY_STRIKE.id));
		toggle(player.getAttribute(Attributes.ARMOR), "skill_resilience", 2.0, AttributeModifier.Operation.ADD_VALUE, data.hasSkill(Skill.RESILIENCE.id));
		toggle(player.getAttribute(Attributes.SAFE_FALL_DISTANCE), "skill_feather_fall", 9.0, AttributeModifier.Operation.ADD_VALUE,
			data.hasSkill(Skill.FEATHER_FALL.id));
	}

	private static void toggle(AttributeInstance attribute, String name, double amount, AttributeModifier.Operation op, boolean on) {
		if (attribute == null) {
			return;
		}
		Identifier id = Celestial.id(name);
		boolean has = attribute.hasModifier(id);
		if (on && !has) {
			attribute.addPermanentModifier(new AttributeModifier(id, amount, op));
		} else if (!on && has) {
			attribute.removeModifier(id);
		}
	}
}
