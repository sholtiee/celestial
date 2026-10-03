package dev.celestial.starlight;

import dev.celestial.data.CelestialData;
import dev.celestial.registry.ModEffects;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** Флакон звёздного света: страх тьмы исчезает, 3 минуты «Звёздного сияния» (страх не растёт, вокруг светло). */
public class StarlightFlaskItem extends Item {
	public static final int DURATION = 20 * 180;

	public StarlightFlaskItem(Properties properties) {
		super(properties);
	}

	@Override
	public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
		if (entity instanceof ServerPlayer player) {
			CelestialData.update(player, d -> d.withFear(0));
			player.addEffect(new MobEffectInstance(ModEffects.STARLIGHT, DURATION, 0, false, true, true));
		}
		return super.finishUsingItem(stack, level, entity);
	}
}
