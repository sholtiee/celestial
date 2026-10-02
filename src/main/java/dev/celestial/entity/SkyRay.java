package dev.celestial.entity;

import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.animal.happyghast.HappyGhast;
import net.minecraft.world.level.Level;

/**
 * Небесный скат: ездовое летающее существо для двоих-четверых. Управление и упряжь — как у счастливого гаста
 * (наследуем его поведение), но быстрее и с собственной моделью.
 */
public class SkyRay extends HappyGhast {
	public SkyRay(EntityType<? extends SkyRay> type, Level level) {
		super(type, level);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return HappyGhast.createAttributes()
			.add(Attributes.MAX_HEALTH, 30.0)
			.add(Attributes.FLYING_SPEED, 0.09)
			.add(Attributes.MOVEMENT_SPEED, 0.09);
	}
}
