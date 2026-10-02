package dev.celestial.registry;

import dev.celestial.Celestial;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;

public final class ModEffects {
	/** Благословение: награда за финал — +2 сердца и удача. */
	public static final Holder<MobEffect> BLESSING = Registry.registerForHolder(BuiltInRegistries.MOB_EFFECT, Celestial.id("blessing"),
		new MobEffect(MobEffectCategory.BENEFICIAL, 0xFFE9A8) {}
			.addAttributeModifier(Attributes.MAX_HEALTH, Celestial.id("blessing_health"), 4.0, AttributeModifier.Operation.ADD_VALUE)
			.addAttributeModifier(Attributes.LUCK, Celestial.id("blessing_luck"), 1.0, AttributeModifier.Operation.ADD_VALUE));

	private ModEffects() {}

	public static void init() {
	}
}
