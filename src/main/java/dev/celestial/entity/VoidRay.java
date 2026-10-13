package dev.celestial.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Пустотный скат — ездовой планер Астрала (упряжь как у Небесного ската). Быстрее и крепче родича, не боится падения:
 * в невесомости это главный способ перелетать между астероидами.
 */
public class VoidRay extends SkyRay {
	public VoidRay(EntityType<? extends VoidRay> type, Level level) {
		super(type, level);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return SkyRay.createAttributes()
			.add(Attributes.MAX_HEALTH, 40.0)
			.add(Attributes.FLYING_SPEED, 0.13)
			.add(Attributes.MOVEMENT_SPEED, 0.13);
	}

	@Override
	public boolean causeFallDamage(double fallDistance, float multiplier, DamageSource source) {
		return false;
	}

	@Override
	protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {
	}
}
