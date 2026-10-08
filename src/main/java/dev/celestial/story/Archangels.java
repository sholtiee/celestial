package dev.celestial.story;

import dev.celestial.entity.Archangel;
import dev.celestial.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.phys.AABB;

/** Четыре архангела сходят к алтарю Цитадели, когда Акт I пройден (LORE §4). Если они уже тут — повторно не появляются. */
public final class Archangels {
	private Archangels() {}

	public static void appear(ServerLevel level, BlockPos altar) {
		if (!level.getEntitiesOfClass(Archangel.class, new AABB(altar).inflate(24)).isEmpty()) {
			return;
		}
		for (int i = 0; i < Archangel.NAMES.length; i++) {
			double a = Math.PI / 2 * i + Math.PI / 4;
			double x = altar.getX() + 0.5 + Math.cos(a) * 5;
			double z = altar.getZ() + 0.5 + Math.sin(a) * 5;
			Archangel angel = ModEntities.ARCHANGEL.create(level, EntitySpawnReason.TRIGGERED);
			if (angel == null) {
				continue;
			}
			angel.setVariant(i);
			float yaw = (float) Math.toDegrees(Math.atan2(altar.getZ() + 0.5 - z, altar.getX() + 0.5 - x)) - 90.0F;
			angel.snapTo(x, altar.getY() + 0.2, z, yaw, 0);
			level.addFreshEntity(angel);
			level.sendParticles(ParticleTypes.END_ROD, x, altar.getY() + 1.4, z, 40, 0.3, 1.0, 0.3, 0.05);
		}
	}
}
