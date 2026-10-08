package dev.celestial.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.celestial.Celestial;
import dev.celestial.entity.CloudWhale;
import dev.celestial.entity.LightWisp;
import dev.celestial.entity.Pegasus;
import dev.celestial.entity.StormSpirit;
import dev.celestial.registry.ModEntities;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.animal.equine.BabyHorseModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.AbstractHorseRenderer;
import net.minecraft.client.renderer.entity.ArrowRenderer;
import net.minecraft.client.renderer.entity.BlazeRenderer;
import net.minecraft.client.renderer.entity.ThrownItemRenderer;
import net.minecraft.client.renderer.entity.state.ArrowRenderState;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.PhantomRenderer;
import net.minecraft.client.renderer.entity.layers.SimpleEquipmentLayer;
import net.minecraft.client.renderer.entity.state.EquineRenderState;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.entity.state.PhantomRenderState;
import net.minecraft.client.model.animal.equine.EquineSaddleModel;
import net.minecraft.client.resources.model.EquipmentClientInfo;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Mob;

public final class CelestialRenderers {
	private CelestialRenderers() {}

	/** Разлом — подкласс сущности портала Энда, поэтому подходит ванильный «звёздный» рендер. */
	@SuppressWarnings("unchecked")
	private static net.minecraft.world.level.block.entity.BlockEntityType<net.minecraft.world.level.block.entity.TheEndPortalBlockEntity> riftType() {
		return (net.minecraft.world.level.block.entity.BlockEntityType<net.minecraft.world.level.block.entity.TheEndPortalBlockEntity>)
			(net.minecraft.world.level.block.entity.BlockEntityType<?>) dev.celestial.registry.ModBlockEntities.ABYSS_RIFT;
	}

	private static Identifier tex(String name) {
		return Celestial.id("textures/entity/" + name + ".png");
	}

	public static void init() {
		ModModelLayers.init();
		AbyssRenderers.init();
		FrozenRenderers.init();
		ArchonRenderer.init();
		CelestialParticle.init();
		net.fabricmc.fabric.api.client.rendering.v1.BlockEntityRendererRegistry.register(
			dev.celestial.registry.ModBlockEntities.BEAM_SOURCE, ctx -> new BeamRenderer());
		net.fabricmc.fabric.api.client.rendering.v1.BlockEntityRendererRegistry.register(
			riftType(), ctx -> new net.minecraft.client.renderer.blockentity.TheEndPortalRenderer());
		GuardianRenderer.register();
		EntityRendererRegistry.register(ModEntities.FALLEN_GUARDIAN, GuardianRenderer::new);
		EntityRendererRegistry.register(ModEntities.ANGEL, AngelRenderer::new);
		EntityRendererRegistry.register(ModEntities.STORM_SPIRIT, StormSpiritRenderer::new);
		EntityRendererRegistry.register(ModEntities.FALLEN_SERAPH, SeraphRenderer::new);
		EntityRendererRegistry.register(ModEntities.SERAPH_CRYSTAL, SeraphRenderer.Crystal::new);
		EntityRendererRegistry.register(ModEntities.WINGED_SERPENT, ctx -> new PhantomRenderer(ctx) {
			@Override
			public Identifier getTextureLocation(PhantomRenderState state) {
				return tex("winged_serpent");
			}
		});
		EntityRendererRegistry.register(ModEntities.CLOUD_WHALE, CloudWhaleRenderer::new);
		EntityRendererRegistry.register(ModEntities.LIGHT_WISP, LightWispRenderer::new);
		EntityRendererRegistry.register(ModEntities.PEGASUS, PegasusRenderer::new);
		EntityRendererRegistry.register(ModEntities.STAR_ARROW, StarArrowRenderer::new);
		EntityRendererRegistry.register(ModEntities.CHERUB, ctx -> new net.minecraft.client.renderer.entity.AllayRenderer(ctx) {
			@Override
			public Identifier getTextureLocation(net.minecraft.client.renderer.entity.state.AllayRenderState state) {
				return tex("cherub");
			}
		});
		EntityRendererRegistry.register(ModEntities.GOLDEN_RAM, ctx -> new net.minecraft.client.renderer.entity.SheepRenderer(ctx) {
			@Override
			public Identifier getTextureLocation(net.minecraft.client.renderer.entity.state.SheepRenderState state) {
				return tex("golden_ram");
			}
		});
		EntityRendererRegistry.register(ModEntities.STORM_ELEMENTAL, ctx -> new StormSpiritRenderer(ctx) {
			@Override
			protected void scale(LivingEntityRenderState state, PoseStack poseStack) {
				poseStack.scale(2.5F, 2.5F, 2.5F);
			}
		});
		EntityRendererRegistry.register(ModEntities.SKY_RAY, ctx -> new SimpleRenderer<>(ctx, new SkyRayModel(ctx.bakeLayer(ModModelLayers.SKY_RAY)),
			tex("sky_ray"), 1.8F, 1.6F, false));
		EntityRendererRegistry.register(ModEntities.CLOUD_JELLY, ctx -> new SimpleRenderer<>(ctx, new CloudJellyModel(ctx.bakeLayer(ModModelLayers.CLOUD_JELLY)),
			tex("cloud_jelly"), 0.6F, 1.4F, true));
		EntityRendererRegistry.register(ModEntities.MIMIC, MimicRenderer::new);
		EntityRendererRegistry.register(ModEntities.LIGHT_SPEAR, ctx -> new ThrownItemRenderer<>(ctx, 1.6F, true));
		EntityRendererRegistry.register(ModEntities.SHADOW, ctx -> new Humanoid<>(ctx, tex("shadow"), 1.0F));
		EntityRendererRegistry.register(ModEntities.METEOR, ctx -> new ThrownItemRenderer<>(ctx, 3.0F, true));
	}

	/** Человекоподобные мобы Рая на общей модели 64×64. Крылья рисует ванильный WingsLayer по предмету в слоте груди. */
	public static class Humanoid<T extends Mob> extends HumanoidMobRenderer<T, HumanoidRenderState, HumanoidModel<HumanoidRenderState>> {
		private final Identifier texture;
		private final float scale;

		public Humanoid(EntityRendererProvider.Context ctx, Identifier texture, float scale) {
			super(ctx, new HumanoidModel<>(ctx.bakeLayer(ModModelLayers.HUMANOID)), 0.5F);
			this.texture = texture;
			this.scale = scale;
		}

		@Override
		public Identifier getTextureLocation(HumanoidRenderState state) {
			return texture;
		}

		@Override
		public HumanoidRenderState createRenderState() {
			return new HumanoidRenderState();
		}

		@Override
		protected void scale(HumanoidRenderState state, PoseStack poseStack) {
			poseStack.scale(scale, scale, scale);
		}
	}

	public static class AngelState extends HumanoidRenderState {
		public int profession;
	}

	static class AngelRenderer extends HumanoidMobRenderer<dev.celestial.entity.Angel, AngelState, HumanoidModel<AngelState>> {
		AngelRenderer(EntityRendererProvider.Context ctx) {
			super(ctx, new HumanoidModel<>(ctx.bakeLayer(ModModelLayers.HUMANOID)), 0.5F);
		}

		@Override
		public Identifier getTextureLocation(AngelState state) {
			return tex("angel_" + dev.celestial.entity.Angel.PROFESSIONS[Math.floorMod(state.profession, 4)]);
		}

		@Override
		public AngelState createRenderState() {
			return new AngelState();
		}

		@Override
		public void extractRenderState(dev.celestial.entity.Angel entity, AngelState state, float partialTicks) {
			super.extractRenderState(entity, state, partialTicks);
			state.profession = entity.getProfession();
		}

		@Override
		protected void scale(AngelState state, PoseStack poseStack) {
			poseStack.scale(0.95F, 0.95F, 0.95F);
		}
	}

	static class StormSpiritRenderer extends BlazeRenderer {
		// (масштаб переопределяется у Грозового элементаля)
		StormSpiritRenderer(EntityRendererProvider.Context ctx) {
			super(ctx);
		}

		@Override
		public Identifier getTextureLocation(LivingEntityRenderState state) {
			return tex("storm_spirit");
		}
	}

	static class CloudWhaleRenderer extends MobRenderer<CloudWhale, LivingEntityRenderState, CloudWhaleModel> {
		CloudWhaleRenderer(EntityRendererProvider.Context ctx) {
			super(ctx, new CloudWhaleModel(ctx.bakeLayer(ModModelLayers.CLOUD_WHALE)), 2.5F);
		}

		@Override
		public Identifier getTextureLocation(LivingEntityRenderState state) {
			return tex("cloud_whale");
		}

		@Override
		public LivingEntityRenderState createRenderState() {
			return new LivingEntityRenderState();
		}

		@Override
		protected void scale(LivingEntityRenderState state, PoseStack poseStack) {
			poseStack.scale(2.0F, 2.0F, 2.0F);
		}
	}

	static class LightWispRenderer extends MobRenderer<LightWisp, LivingEntityRenderState, LightWispModel> {
		LightWispRenderer(EntityRendererProvider.Context ctx) {
			super(ctx, new LightWispModel(ctx.bakeLayer(ModModelLayers.LIGHT_WISP)), 0.15F);
		}

		@Override
		public Identifier getTextureLocation(LivingEntityRenderState state) {
			return tex("light_wisp");
		}

		@Override
		public LivingEntityRenderState createRenderState() {
			return new LivingEntityRenderState();
		}

		@Override
		protected int getBlockLightLevel(LightWisp entity, BlockPos pos) {
			return 15;
		}
	}

	/** Рендер «модель + текстура + масштаб» для простых существ. */
	static class SimpleRenderer<T extends net.minecraft.world.entity.Mob> extends MobRenderer<T, LivingEntityRenderState, net.minecraft.client.model.EntityModel<LivingEntityRenderState>> {
		private final Identifier texture;
		private final float scale;
		private final boolean glow;

		SimpleRenderer(EntityRendererProvider.Context ctx, net.minecraft.client.model.EntityModel<LivingEntityRenderState> model, Identifier texture,
			float shadow, float scale, boolean glow) {
			super(ctx, model, shadow);
			this.texture = texture;
			this.scale = scale;
			this.glow = glow;
		}

		@Override
		public Identifier getTextureLocation(LivingEntityRenderState state) {
			return texture;
		}

		@Override
		public LivingEntityRenderState createRenderState() {
			return new LivingEntityRenderState();
		}

		@Override
		protected void scale(LivingEntityRenderState state, PoseStack poseStack) {
			poseStack.scale(scale, scale, scale);
		}

		@Override
		protected int getBlockLightLevel(T entity, BlockPos pos) {
			return glow ? Math.max(12, super.getBlockLightLevel(entity, pos)) : super.getBlockLightLevel(entity, pos);
		}
	}

	static class MimicRenderer extends MobRenderer<dev.celestial.entity.Mimic, MimicModel.State, MimicModel> {
		MimicRenderer(EntityRendererProvider.Context ctx) {
			super(ctx, new MimicModel(ctx.bakeLayer(ModModelLayers.MIMIC)), 0.5F);
		}

		@Override
		public Identifier getTextureLocation(MimicModel.State state) {
			return tex("mimic");
		}

		@Override
		public MimicModel.State createRenderState() {
			return new MimicModel.State();
		}

		@Override
		public void extractRenderState(dev.celestial.entity.Mimic entity, MimicModel.State state, float partialTicks) {
			super.extractRenderState(entity, state, partialTicks);
			state.awake = entity.isAwake();
		}
	}

	static class StarArrowRenderer extends ArrowRenderer<dev.celestial.entity.StarArrow, ArrowRenderState> {
		StarArrowRenderer(EntityRendererProvider.Context ctx) {
			super(ctx);
		}

		@Override
		protected Identifier getTextureLocation(ArrowRenderState state) {
			return Celestial.id("textures/entity/projectiles/star_arrow.png");
		}

		@Override
		public ArrowRenderState createRenderState() {
			return new ArrowRenderState();
		}
	}

	public static class PegasusRenderState extends EquineRenderState {
		public int variant;
	}

	static class PegasusRenderer extends AbstractHorseRenderer<Pegasus, PegasusRenderState, net.minecraft.client.model.EntityModel<EquineRenderState>> {
		private static final Identifier[] TEXTURES = {tex("pegasus"), tex("pegasus_golden"), tex("pegasus_storm")};

		PegasusRenderer(EntityRendererProvider.Context ctx) {
			super(ctx, new PegasusModel(ctx.bakeLayer(ModModelLayers.PEGASUS)), new BabyHorseModel(ctx.bakeLayer(ModelLayers.HORSE_BABY)));
			this.addLayer(new SimpleEquipmentLayer<>(this, ctx.getEquipmentRenderer(), EquipmentClientInfo.LayerType.HORSE_BODY,
				state -> state.bodyArmorItem, new net.minecraft.client.model.animal.equine.HorseModel(ctx.bakeLayer(ModelLayers.HORSE_ARMOR)), null, 2));
			this.addLayer(new SimpleEquipmentLayer<>(this, ctx.getEquipmentRenderer(), EquipmentClientInfo.LayerType.HORSE_SADDLE,
				state -> state.saddle, new EquineSaddleModel(ctx.bakeLayer(ModelLayers.HORSE_SADDLE)), null, 2));
		}

		@Override
		public Identifier getTextureLocation(PegasusRenderState state) {
			return state.isBaby ? tex("pegasus_baby") : TEXTURES[Math.floorMod(state.variant, TEXTURES.length)];
		}

		@Override
		public PegasusRenderState createRenderState() {
			return new PegasusRenderState();
		}

		@Override
		public void extractRenderState(Pegasus entity, PegasusRenderState state, float partialTicks) {
			super.extractRenderState(entity, state, partialTicks);
			state.variant = entity.getVariant();
		}
	}
}
