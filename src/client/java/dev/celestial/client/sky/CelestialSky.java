package dev.celestial.client.sky;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.BufferBuilder;
import com.mojang.blaze3d.vertex.ByteBufferBuilder;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.MeshData;
import com.mojang.math.Axis;
import com.mojang.renderpearl.api.buffers.GpuBuffer;
import com.mojang.renderpearl.api.buffers.GpuBufferSlice;
import com.mojang.renderpearl.api.commands.RenderPass;
import com.mojang.renderpearl.api.pipeline.PrimitiveTopology;
import dev.celestial.Celestial;
import dev.celestial.astral.Choir;
import dev.celestial.astral.Choirs;
import dev.celestial.client.ClientState;
import dev.celestial.client.grace.GraceClient;
import dev.celestial.world.HeavenDimension;
import dev.celestial.world.dim.AbyssFeatures;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.client.renderer.state.level.SkyRenderState;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import org.joml.Matrix4f;
import org.joml.Matrix4fStack;
import org.joml.Vector3f;
import org.joml.Vector4f;

/**
 * Небо мода (O5, шаг 5). Спрайты — в атласе небесных тел ванилли (папка {@code textures/environment/celestial} собирается из всех
 * пространств имён), рисуются тем же конвейером, что солнце и луна (светят, складываясь с небом).
 * <ul>
 *   <li>Рай: ореол вокруг солнца днём, полярное сияние на севере ночью, звёзды видны и днём.</li>
 *   <li>Рай после «Поглотить»: небо темнеет до лилового сумрака, звёзды горят всегда, ореол — тусклый и багровый.</li>
 *   <li>Астрал: три туманности и созвездия собранных хоров — каждое на своём месте небосвода, загорается, когда хор собран.</li>
 * </ul>
 */
public final class CelestialSky {
	private enum Kind { NONE, HEAVEN, HEAVEN_DARK, ASTRAL }

	private static Kind kind = Kind.NONE;
	private static final Map<Identifier, GpuBuffer> QUADS = new HashMap<>();
	private static final Map<Identifier, float[]> UVS = new HashMap<>();

	private CelestialSky() {}

	/** После ванильного заполнения состояния неба: поправить его под измерение мода и запомнить, что рисовать. */
	public static void extract(ClientLevel level, SkyRenderState state) {
		var dim = level.dimension();
		if (dim == HeavenDimension.HEAVEN) {
			boolean dark = "consume".equals(ClientState.ending());
			kind = dark ? Kind.HEAVEN_DARK : Kind.HEAVEN;
			if (state.skyColor != null) {
				if (dark) {
					state.skyColor = new Vector3f(state.skyColor).mul(0.22F).add(0.08F, 0.02F, 0.12F);
					state.starBrightness = 1.0F;
				} else {
					state.starBrightness = Math.max(state.starBrightness, 0.35F);  // звёзды Рая видны и днём
				}
			}
		} else if (dim == AbyssFeatures.ASTRAL) {
			kind = Kind.ASTRAL;
			state.starBrightness = 1.0F;
		} else {
			kind = Kind.NONE;
		}
	}

	/** После солнца, луны и звёзд. sunAngle — в радианах (0 — полдень). */
	public static void draw(RenderPass pass, TextureAtlas atlas, RenderSystem.AutoStorageIndexBuffer indices, float sunAngle, float rain) {
		if (kind == Kind.NONE) {
			return;
		}
		float day = Math.max(0.0F, Mth.cos(sunAngle));
		float night = Math.max(0.0F, -Mth.cos(sunAngle));
		switch (kind) {
			case HEAVEN, HEAVEN_DARK -> {
				boolean dark = kind == Kind.HEAVEN_DARK;
				// ореол солнца: большой мягкий венец вокруг диска
				Matrix4f m = base().rotate(Axis.YP.rotationDegrees(-90)).rotate(Axis.XP.rotation(sunAngle)).translate(0, 100, 0).scale(80, 1, 80);
				quad(pass, atlas, indices, "halo", m, dark ? new Vector4f(0.5F, 0.08F, 0.12F, 0.6F * day * rain) : new Vector4f(1.0F, 0.9F, 0.6F, 0.7F * day * rain));
				// полярное сияние — занавеси низко над северным горизонтом, ночью (в тёмном Раю — всегда, багровое)
				float aurora = dark ? 0.8F : night * rain;
				if (aurora > 0.01F) {
					for (int k = 0; k < 5; k++) {
						Matrix4f a = base().rotate(Axis.YP.rotationDegrees(180 + (k - 2) * 24)).rotate(Axis.XP.rotationDegrees(62 + (k % 2) * 6))
							.translate(0, 100, 0).scale(30, 1, 16);
						Vector4f col = dark ? new Vector4f(0.8F, 0.15F, 0.35F, 0.55F * aurora) : new Vector4f(0.55F, 1.0F, 0.85F, 0.6F * aurora);
						quad(pass, atlas, indices, "aurora", a, col);
					}
				}
			}
			case ASTRAL -> {
				// туманности на неподвижных местах небосвода
				float[][] nebulae = {{30, 40, 70}, {160, 25, 90}, {260, 55, 60}};
				String[] tex = {"nebula_1", "nebula_2", "nebula_3"};
				for (int i = 0; i < nebulae.length; i++) {
					Matrix4f n = base().rotate(Axis.YP.rotationDegrees(nebulae[i][0])).rotate(Axis.XP.rotationDegrees(nebulae[i][1]))
						.translate(0, 100, 0).scale(nebulae[i][2], 1, nebulae[i][2]);
					quad(pass, atlas, indices, tex[i], n, new Vector4f(1, 1, 1, 0.85F));
				}
				// созвездия хоров: собранный — ярко, виденный в Телескоп — тускло
				var d = GraceClient.data();
				for (Choir c : Choir.values()) {
					boolean got = Choirs.collected(d, c);
					boolean seen = got || d.knows("constellation:" + c.id);
					if (!seen) {
						continue;
					}
					float bright = got ? 1.0F : 0.3F;
					for (int[] p : c.points) {
						Matrix4f s = base().rotate(Axis.YP.rotationDegrees(c.ordinal() * 40.0F + 10)).rotate(Axis.XP.rotationDegrees(42))
							.translate(p[0] * 4.5F, 100, p[1] * 4.5F).scale(p[0] == 0 && p[1] == 0 ? 2.4F : 1.6F, 1, p[0] == 0 && p[1] == 0 ? 2.4F : 1.6F);
						quad(pass, atlas, indices, "choir_star", s, new Vector4f(1.0F, 0.95F, 0.8F, bright));
					}
				}
			}
			default -> { }
		}
	}

	private static Matrix4f base() {
		Matrix4fStack mv = RenderSystem.getModelViewStack();
		return new Matrix4f(mv);
	}

	private static void quad(RenderPass pass, TextureAtlas atlas, RenderSystem.AutoStorageIndexBuffer indices, String sprite, Matrix4f model, Vector4f color) {
		if (color.w <= 0.003F) {
			return;
		}
		Identifier id = Celestial.id(sprite);
		TextureAtlasSprite s = atlas.getSprite(id);
		float[] uv = {s.getU0(), s.getV0(), s.getU1(), s.getV1()};
		GpuBuffer buffer = QUADS.get(id);
		float[] old = UVS.get(id);
		if (buffer == null || old == null || !java.util.Arrays.equals(old, uv)) {  // атлас пересобран (смена ресурсов) — новые координаты
			if (buffer != null) {
				buffer.close();
			}
			buffer = build(sprite, uv);
			QUADS.put(id, buffer);
			UVS.put(id, uv);
		}
		GpuBufferSlice transforms = RenderSystem.getDynamicUniforms().writeTransform(model, color);
		pass.pushDebugGroup(() -> "Celestial sky " + sprite);
		pass.setPipeline(RenderSystem.getCompiledPipeline(RenderPipelines.CELESTIAL));
		RenderSystem.bindDefaultUniforms(pass);
		pass.setUniform("DynamicTransforms", transforms);
		pass.setUniform("Sampler0", atlas.getTextureView(), atlas.getSampler());
		pass.setVertexBuffer(0, buffer.slice());
		pass.setIndexBuffer(indices.getBuffer(6), indices.type());
		pass.drawIndexed(6, 1, 0, 0, 0);
		pass.popDebugGroup();
	}

	private static GpuBuffer build(String name, float[] uv) {
		var format = DefaultVertexFormat.POSITION_TEX;
		try (ByteBufferBuilder bytes = ByteBufferBuilder.exactlySized(4 * format.getVertexSize())) {
			BufferBuilder b = new BufferBuilder(bytes, PrimitiveTopology.QUADS, format);
			b.addVertex(-1.0F, 0.0F, -1.0F).setUv(uv[0], uv[1]);
			b.addVertex(1.0F, 0.0F, -1.0F).setUv(uv[2], uv[1]);
			b.addVertex(1.0F, 0.0F, 1.0F).setUv(uv[2], uv[3]);
			b.addVertex(-1.0F, 0.0F, 1.0F).setUv(uv[0], uv[3]);
			try (MeshData mesh = b.buildOrThrow()) {
				return RenderSystem.getDevice().createBuffer(() -> "Celestial sky " + name, 32, mesh.vertexBuffer());
			}
		}
	}
}
