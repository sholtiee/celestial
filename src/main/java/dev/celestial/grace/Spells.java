package dev.celestial.grace;

import dev.celestial.data.BeaconNetwork;
import dev.celestial.data.CelestialData;
import dev.celestial.data.PlayerData;
import dev.celestial.entity.LightSpear;
import java.util.Comparator;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.EntityTypeTags;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.portal.TeleportTransition;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/** Заклинания Сияния (выполняются на сервере по пакету CastSpell). */
public final class Spells {
	private Spells() {}

	public static void cast(ServerPlayer player, int index) {
		Spell[] all = Spell.values();
		if (index < 0 || index >= all.length) {
			return;
		}
		Spell spell = all[index];
		PlayerData data = CelestialData.get(player);
		if (spell.requires != null && !data.hasSkill(spell.requires.id)) {
			player.sendOverlayMessage(Component.translatable("spell.celestial.unknown"));
			return;
		}
		if (data.radiance() < spell.cost && !player.getAbilities().instabuild) {
			player.sendOverlayMessage(Component.translatable("spell.celestial.no_radiance"));
			player.level().playSound(null, player.blockPosition(), SoundEvents.NOTE_BLOCK_BASS.value(), SoundSource.PLAYERS, 0.6F, 0.5F);
			return;
		}
		boolean ok = switch (spell) {
			case SCOUTS -> scouts(player);
			case LIGHT_BOLT -> lightBolt(player);
			case HEALING_LIGHT -> heal(player);
			case LIGHT_SHIELD -> shield(player);
			case BEACON_RECALL -> recall(player);
			case STARFALL -> starfall(player);
			case FLASH -> flash(player);
		};
		if (ok && !player.getAbilities().instabuild) {
			CelestialData.update(player, d -> d.withRadiance(d.radiance() - spell.cost));
		}
	}

	private static boolean scouts(ServerPlayer player) {
		var mobs = player.level().getEntitiesOfClass(LivingEntity.class, player.getBoundingBox().inflate(32), e -> e instanceof Enemy);
		mobs.forEach(m -> m.addEffect(new MobEffectInstance(MobEffects.GLOWING, 200)));
		player.level().sendParticles(ParticleTypes.WAX_OFF, player.getX(), player.getY(1.0), player.getZ(), 40, 2, 1, 2, 0.5);
		player.level().playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.0F, 1.6F);
		player.sendOverlayMessage(Component.translatable("spell.celestial.scouts.result", mobs.size()));
		return true;
	}

	private static boolean lightBolt(ServerPlayer player) {
		ServerLevel level = player.level();
		Vec3 eye = player.getEyePosition();
		Vec3 end = eye.add(player.getLookAngle().scale(24));
		HitResult block = level.clip(new ClipContext(eye, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
		if (block.getType() != HitResult.Type.MISS) {
			end = block.getLocation();
		}
		EntityHitResult hit = ProjectileUtil.getEntityHitResult(player, eye, end, new AABB(eye, end).inflate(1), e -> e instanceof LivingEntity && e != player, 24 * 24);
		Vec3 stop = hit != null ? hit.getLocation() : end;
		for (double t = 0; t < 1; t += 0.04) {
			Vec3 p = eye.lerp(stop, t);
			level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 1, 0, 0, 0, 0);
		}
		if (hit != null && hit.getEntity() instanceof LivingEntity target) {
			float dmg = target.is(EntityTypeTags.UNDEAD) ? 11.0F : 7.0F;
			target.hurtServer(level, level.damageSources().indirectMagic(player, player), dmg);
			target.addEffect(new MobEffectInstance(MobEffects.GLOWING, 100));
		}
		level.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.0F, 2.0F);
		return true;
	}

	private static boolean heal(ServerPlayer player) {
		player.heal(6.0F);
		player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 100, 0));
		player.level().sendParticles(ParticleTypes.HEART, player.getX(), player.getY(1.0), player.getZ(), 6, 0.5, 0.5, 0.5, 0);
		player.level().playSound(null, player.blockPosition(), SoundEvents.ALLAY_ITEM_GIVEN, SoundSource.PLAYERS, 1.0F, 1.2F);
		return true;
	}

	private static boolean shield(ServerPlayer player) {
		player.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, 300, 1));
		player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 200, 0));
		player.level().sendParticles(ParticleTypes.END_ROD, player.getX(), player.getY(0.5), player.getZ(), 30, 0.6, 0.8, 0.6, 0.02);
		player.level().playSound(null, player.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 1.0F, 1.4F);
		return true;
	}

	private static boolean recall(ServerPlayer player) {
		String dim = player.level().dimension().identifier().toString();
		BeaconNetwork.Beacon nearest = CelestialData.beacons(player.level().getServer()).beacons().stream()
			.filter(b -> b.dimension().equals(dim))
			.min(Comparator.comparingDouble(b -> b.pos().distSqr(player.blockPosition()))).orElse(null);
		if (nearest == null) {
			player.sendOverlayMessage(Component.translatable("spell.celestial.recall.none"));
			return false;
		}
		BlockPos to = nearest.pos().above();
		player.teleport(new TeleportTransition(player.level(), Vec3.atBottomCenterOf(to), Vec3.ZERO, player.getYRot(), player.getXRot(),
			TeleportTransition.PLAY_PORTAL_SOUND));
		return true;
	}

	private static boolean starfall(ServerPlayer player) {
		ServerLevel level = player.level();
		Vec3 eye = player.getEyePosition();
		HitResult hit = level.clip(new ClipContext(eye, eye.add(player.getLookAngle().scale(40)), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
		Vec3 at = hit.getLocation();
		for (int i = 0; i < 8; i++) {
			LightSpear spear = LightSpear.hostile(level, player, at.x + (level.getRandom().nextDouble() - 0.5) * 6,
				at.y + 16 + level.getRandom().nextInt(6), at.z + (level.getRandom().nextDouble() - 0.5) * 6);
			level.addFreshEntity(spear);
		}
		level.playSound(null, BlockPos.containing(at), SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.PLAYERS, 2.0F, 0.6F);
		return true;
	}

	private static boolean flash(ServerPlayer player) {
		ServerLevel level = player.level();
		for (Entity e : level.getEntities(player, player.getBoundingBox().inflate(8), e -> e instanceof Enemy && e instanceof LivingEntity)) {
			LivingEntity mob = (LivingEntity) e;
			mob.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 100));
			mob.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 100, 2));
			mob.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 1));
			Vec3 push = mob.position().subtract(player.position()).normalize().scale(1.2);
			mob.push(push.x, 0.4, push.z);
		}
		level.sendParticles(ParticleTypes.END_ROD, player.getX(), player.getY(1.0), player.getZ(), 80, 3, 1, 3, 0.4);
		level.playSound(null, player.blockPosition(), SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.PLAYERS, 1.0F, 1.8F);
		return true;
	}
}
