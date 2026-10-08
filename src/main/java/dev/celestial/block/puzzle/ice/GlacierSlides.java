package dev.celestial.block.puzzle.ice;

import com.mojang.math.Transformation;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import org.joml.Vector3f;

/**
 * Едущие глыбы. Пока глыба скользит, вместо блока летит {@link Display.BlockDisplay} с плавной интерполяцией сдвига
 * (клиент сам сглаживает), а в конце пути глыба снова становится блоком и зал проверяет решение.
 */
public final class GlacierSlides {
	/** Тиков на клетку пути. */
	private static final int TICKS_PER_CELL = 2;

	private static final class Slide {
		final ServerLevel level;
		final BlockPos from;
		final BlockPos to;
		final Direction dir;
		final BlockState state;
		final GlacierHallBlockEntity hall;
		final Player player;
		final int duration;
		Display.BlockDisplay display;
		int age;

		Slide(ServerLevel level, BlockPos from, BlockPos to, Direction dir, BlockState state, GlacierHallBlockEntity hall, Player player) {
			this.level = level;
			this.from = from;
			this.to = to;
			this.dir = dir;
			this.state = state;
			this.hall = hall;
			this.player = player;
			this.duration = Math.max(4, from.distManhattan(to) * TICKS_PER_CELL);
		}
	}

	private static final List<Slide> ACTIVE = new ArrayList<>();

	private GlacierSlides() {}

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(server -> tick());
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			for (Slide s : ACTIVE) {
				finish(s, false);
			}
			ACTIVE.clear();
		});
	}

	public static boolean busy(GlacierHallBlockEntity hall) {
		for (Slide s : ACTIVE) {
			if (s.hall == hall) {
				return true;
			}
		}
		return false;
	}

	/** Запустить глыбу из from в to (путь уже проверен залом). Чужие блоки на пути глыба сметает. */
	static void start(ServerLevel level, BlockPos from, BlockPos to, Direction dir, GlacierHallBlockEntity hall, Player player) {
		BlockState state = level.getBlockState(from);
		Slide slide = new Slide(level, from.immutable(), to.immutable(), dir, state, hall, player);
		level.setBlock(from, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
		for (BlockPos p = from.relative(dir); ; p = p.relative(dir)) {
			if (!level.getBlockState(p).isAir()) {
				level.destroyBlock(p, true);  // свой блок-стопор не останавливает глыбу
			}
			if (p.equals(to)) {
				break;
			}
		}
		Display.BlockDisplay display = net.minecraft.world.entity.EntityTypes.BLOCK_DISPLAY.create(level, EntitySpawnReason.TRIGGERED);
		if (display != null) {
			display.setBlockState(state);
			display.setPos(from.getX(), from.getY(), from.getZ());
			level.addFreshEntity(display);
			slide.display = display;
		}
		level.playSound(null, from, dev.celestial.registry.ModSounds.GLACIER_SLIDE, SoundSource.BLOCKS, 1.0F, 0.9F + level.getRandom().nextFloat() * 0.2F);
		ACTIVE.add(slide);
	}

	private static void tick() {
		Iterator<Slide> it = ACTIVE.iterator();
		while (it.hasNext()) {
			Slide s = it.next();
			s.age++;
			if (s.age == 1 && s.display != null) {
				// со второго тика: клиент уже знает о сущности и плавно сдвигает её к цели
				Vector3f shift = new Vector3f(s.to.getX() - s.from.getX(), 0, s.to.getZ() - s.from.getZ());
				s.display.setTransformationInterpolationDelay(0);
				s.display.setTransformationInterpolationDuration(s.duration);
				s.display.setTransformation(new Transformation(shift, null, null, null));
			}
			if (s.age > 1 && s.age <= s.duration + 1) {
				double t = (s.age - 1) / (double) s.duration;
				double x = s.from.getX() + 0.5 + (s.to.getX() - s.from.getX()) * t;
				double z = s.from.getZ() + 0.5 + (s.to.getZ() - s.from.getZ()) * t;
				s.level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState()),
					x, s.from.getY() + 0.05, z, 3, 0.3, 0.02, 0.3, 0.05);
				s.level.sendParticles(ParticleTypes.SNOWFLAKE, x, s.from.getY() + 0.6, z, 1, 0.3, 0.3, 0.3, 0.01);
			}
			if (s.age >= s.duration + 2) {
				finish(s, true);
				it.remove();
			}
		}
	}

	private static void finish(Slide s, boolean notify) {
		if (!s.level.getBlockState(s.to).isAir()) {
			s.level.destroyBlock(s.to, true);
		}
		s.level.setBlock(s.to, s.state, Block.UPDATE_ALL);
		if (s.display != null) {
			s.display.discard();
		}
		s.level.playSound(null, s.to, SoundEvents.GLASS_PLACE, SoundSource.BLOCKS, 1.2F, 0.5F);
		s.level.sendParticles(ParticleTypes.SNOWFLAKE, s.to.getX() + 0.5, s.to.getY() + 0.5, s.to.getZ() + 0.5, 12, 0.4, 0.4, 0.4, 0.04);
		if (notify) {
			s.hall.afterMove(s.level, s.player);
		}
	}
}
