package dev.celestial.item;

import dev.celestial.entity.StarArrow;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.BowItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** Звёздный лук: стреляет самонаводящимися звёздными стрелами (расходует обычные стрелы). */
public class StarbowItem extends BowItem {
	public StarbowItem(Properties properties) {
		super(properties);
	}

	@Override
	protected Projectile createProjectile(Level level, LivingEntity shooter, ItemStack weapon, ItemStack projectile, boolean isCrit) {
		StarArrow arrow = new StarArrow(level, shooter, projectile.copyWithCount(1), weapon);
		arrow.setCritArrow(isCrit);
		return arrow;
	}
}
