package dev.celestial.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.celestial.Celestial;
import dev.celestial.entity.BrassDoll;
import dev.celestial.entity.ClockworkHorse;
import dev.celestial.entity.ClockworkSentry;
import dev.celestial.entity.Ophanim;
import dev.celestial.entity.WinderBeetle;
import dev.celestial.registry.ModEntities;
import java.util.function.Function;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;

/** Рендеры существ Хронограда: свои модели + светящийся слой `<имя>_glow.png`. */
public final class ChronoRenderers {
	private ChronoRenderers() {}

	public static void init() {
		register(ModEntities.CLOCKWORK_SENTRY, "clockwork_sentry", ChronoModels.Sentry::createLayer, ChronoModels.Sentry::new, 0.6F, 1.0F);
		register(ModEntities.WINDER_BEETLE, "winder_beetle", ChronoModels.Beetle::createLayer, ChronoModels.Beetle::new, 0.35F, 1.0F);
		register(ModEntities.BRASS_DOLL, "brass_doll", ChronoModels.Doll::createLayer, ChronoModels.Doll::new, 0.45F, 0.95F);
		register(ModEntities.OPHANIM, "ophanim", ChronoModels.Ophanim::createLayer, ChronoModels.Ophanim::new, 0.0F, 1.3F);
		register(ModEntities.CLOCKWORK_HORSE, "clockwork_horse", ChronoModels.Horse::createLayer, ChronoModels.Horse::new, 0.75F, 1.1F);
	}

	private static <T extends Mob> void register(EntityType<T> type, String name, java.util.function.Supplier<LayerDefinition> layer,
		Function<ModelPart, EntityModel<ChronoModels.State>> model, float shadow, float scale) {
		ModelLayerLocation location = new ModelLayerLocation(Celestial.id(name), "main");
		ModelLayerRegistry.registerModelLayer(location, layer::get);
		EntityRendererRegistry.register(type, ctx -> new Renderer<>(ctx, model.apply(ctx.bakeLayer(location)), name, shadow, scale));
	}

	static class Renderer<T extends Mob> extends MobRenderer<T, ChronoModels.State, EntityModel<ChronoModels.State>> {
		private final Identifier texture;
		private final float scale;

		Renderer(EntityRendererProvider.Context ctx, EntityModel<ChronoModels.State> model, String name, float shadow, float scale) {
			super(ctx, model, shadow);
			this.texture = Celestial.id("textures/entity/" + name + ".png");
			this.scale = scale;
			addLayer(new AbyssRenderers.GlowLayer<>(this, Celestial.id("textures/entity/" + name + "_glow.png")));
		}

		@Override
		public Identifier getTextureLocation(ChronoModels.State state) {
			return texture;
		}

		@Override
		public ChronoModels.State createRenderState() {
			return new ChronoModels.State();
		}

		@Override
		public void extractRenderState(T entity, ChronoModels.State state, float partialTicks) {
			super.extractRenderState(entity, state, partialTicks);
			state.attack = 0;
			state.rewind = 0;
			state.beam = 0;
			if (entity instanceof ClockworkSentry sentry) {
				state.attack = sentry.attackProgress(partialTicks);
				state.rewind = sentry.rewinding() / (float) ClockworkSentry.REWIND_TICKS;
				state.wound = sentry.rewinding() == 0;
			} else if (entity instanceof WinderBeetle beetle) {
				state.wound = beetle.wound();
			} else if (entity instanceof BrassDoll doll) {
				state.attack = doll.attackProgress(partialTicks);
			} else if (entity instanceof Ophanim ophanim) {
				state.beam = ophanim.beamProgress(partialTicks);
			} else if (entity instanceof ClockworkHorse horse) {
				state.wound = horse.wind() > 0;
				state.saddled = horse.isSaddled();
				state.ridden = horse.isVehicle();
			}
		}

		@Override
		protected void scale(ChronoModels.State state, PoseStack poseStack) {
			float s = state.isBaby ? scale * 0.5F : scale;
			poseStack.scale(s, s, s);
		}
	}
}
