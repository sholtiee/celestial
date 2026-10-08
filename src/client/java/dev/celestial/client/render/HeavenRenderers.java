package dev.celestial.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.celestial.Celestial;
import dev.celestial.registry.ModEntities;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Mob;

/** Рендеры существ со своими моделями из {@link HeavenModels} + светящийся слой `<имя>_glow.png`. */
public final class HeavenRenderers {
	public static final ModelLayerLocation SHADOW = new ModelLayerLocation(Celestial.id("shadow"), "main");
	public static final ModelLayerLocation STORM = new ModelLayerLocation(Celestial.id("storm_spirit"), "main");
	public static final ModelLayerLocation ANGEL = new ModelLayerLocation(Celestial.id("angel"), "main");
	public static final ModelLayerLocation CHERUB = new ModelLayerLocation(Celestial.id("cherub"), "main");
	public static final ModelLayerLocation SERPENT = new ModelLayerLocation(Celestial.id("winged_serpent"), "main");
	public static final ModelLayerLocation RAM = new ModelLayerLocation(Celestial.id("golden_ram"), "main");

	private HeavenRenderers() {}

	public static void init() {
		ModelLayerRegistry.registerModelLayer(SHADOW, HeavenModels.Shadow::createLayer);
		ModelLayerRegistry.registerModelLayer(STORM, HeavenModels.Storm::createLayer);
		ModelLayerRegistry.registerModelLayer(ANGEL, HeavenModels.Angel::createLayer);
		ModelLayerRegistry.registerModelLayer(CHERUB, HeavenModels.Cherub::createLayer);
		// у ангела четыре профессии — четыре текстуры (одеяние, отделка, рукава)
		EntityRendererRegistry.register(ModEntities.ANGEL, ctx -> new Renderer<>(ctx, new HeavenModels.Angel(ctx.bakeLayer(ANGEL)), "angel", 0.5F, 0.95F) {
			@Override
			public Identifier getTextureLocation(HeavenModels.State state) {
				return Celestial.id("textures/entity/angel_" + dev.celestial.entity.Angel.PROFESSIONS[Math.floorMod(state.variant, 4)] + ".png");
			}

			@Override
			public void extractRenderState(dev.celestial.entity.Angel entity, HeavenModels.State state, float partialTicks) {
				super.extractRenderState(entity, state, partialTicks);
				state.variant = entity.getProfession();
			}
		});
		EntityRendererRegistry.register(ModEntities.CHERUB,
			ctx -> new Renderer<>(ctx, new HeavenModels.Cherub(ctx.bakeLayer(CHERUB)), "cherub", 0.3F, 1.0F));
		ModelLayerRegistry.registerModelLayer(SERPENT, HeavenModels.Serpent::createLayer);
		ModelLayerRegistry.registerModelLayer(RAM, HeavenModels.Ram::createLayer);
		EntityRendererRegistry.register(ModEntities.WINGED_SERPENT, ctx -> new Renderer<>(ctx, new HeavenModels.Serpent(ctx.bakeLayer(SERPENT)), "winged_serpent", 0.6F, 1.0F) {
			@Override
			public void extractRenderState(dev.celestial.entity.WingedSerpent entity, HeavenModels.State state, float partialTicks) {
				super.extractRenderState(entity, state, partialTicks);
				state.flap = entity.getUniqueFlapTickOffset() + state.ageInTicks;
			}

			@Override
			protected void setupRotations(HeavenModels.State state, PoseStack poseStack, float bodyRot, float entityScale) {
				super.setupRotations(state, poseStack, bodyRot, entityScale);
				poseStack.rotateDegrees(com.mojang.math.Axis.XP, state.xRot);  // пикирует носом вниз, как фантом
			}
		});
		EntityRendererRegistry.register(ModEntities.GOLDEN_RAM, ctx -> new Renderer<>(ctx, new HeavenModels.Ram(ctx.bakeLayer(RAM)), "golden_ram", 0.7F, 1.0F) {
			@Override
			public void extractRenderState(dev.celestial.entity.GoldenRam entity, HeavenModels.State state, float partialTicks) {
				super.extractRenderState(entity, state, partialTicks);
				state.eatPos = entity.getHeadEatPositionScale(partialTicks);
				state.eatAngle = entity.getHeadEatAngleScale(partialTicks);
				state.sheared = entity.isSheared();
			}

			@Override
			protected void scale(HeavenModels.State state, PoseStack poseStack) {
				if (state.isBaby) {
					poseStack.scale(0.55F, 0.55F, 0.55F);
				}
			}
		});
		EntityRendererRegistry.register(ModEntities.SHADOW,
			ctx -> new Renderer<>(ctx, new HeavenModels.Shadow(ctx.bakeLayer(SHADOW)), "shadow", 0.4F, 1.0F));
		EntityRendererRegistry.register(ModEntities.STORM_SPIRIT,
			ctx -> new Renderer<>(ctx, new HeavenModels.Storm(ctx.bakeLayer(STORM)), "storm_spirit", 0.4F, 1.0F));
		EntityRendererRegistry.register(ModEntities.STORM_ELEMENTAL,
			ctx -> new Renderer<>(ctx, new HeavenModels.Storm(ctx.bakeLayer(STORM)), "storm_elemental", 1.0F, 2.2F));
	}

	static class Renderer<T extends Mob> extends MobRenderer<T, HeavenModels.State, EntityModel<HeavenModels.State>> {
		private final Identifier texture;
		private final float scale;

		Renderer(EntityRendererProvider.Context ctx, EntityModel<HeavenModels.State> model, String name, float shadow, float scale) {
			super(ctx, model, shadow);
			this.texture = Celestial.id("textures/entity/" + name + ".png");
			this.scale = scale;
			addLayer(new AbyssRenderers.GlowLayer<>(this, Celestial.id("textures/entity/" + name + "_glow.png")));
		}

		@Override
		public Identifier getTextureLocation(HeavenModels.State state) {
			return texture;
		}

		@Override
		public HeavenModels.State createRenderState() {
			return new HeavenModels.State();
		}

		@Override
		public void extractRenderState(T entity, HeavenModels.State state, float partialTicks) {
			super.extractRenderState(entity, state, partialTicks);
			state.attack = entity.getSwingAnimation(partialTicks);
		}

		@Override
		protected void scale(HeavenModels.State state, PoseStack poseStack) {
			poseStack.scale(scale, scale, scale);
		}
	}
}
