package dev.celestial.block.light;

import dev.celestial.light.BeamTarget;
import dev.celestial.light.LightBeams;
import dev.celestial.light.LightColor;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.EnumProperty;

/** Приёмник света: пока в него бьёт луч нужного цвета (белый приёмник принимает любой), выдаёт сигнал 15. */
public class LightReceiverBlock extends Block implements BeamTarget, Rotatable {
	public static final EnumProperty<LightColor> COLOR = EnumProperty.create("color", LightColor.class);
	public static final BooleanProperty POWERED = BooleanProperty.create("powered");
	private static final Map<Long, Long> LAST_HIT = new ConcurrentHashMap<>();

	public LightReceiverBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(COLOR, LightColor.WHITE).setValue(POWERED, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(COLOR, POWERED);
	}

	public static boolean accepts(BlockState state, LightColor color) {
		LightColor wanted = state.getValue(COLOR);
		return wanted == LightColor.WHITE || wanted == color;
	}

	@Override
	public void onBeamHit(ServerLevel level, BlockPos pos, BlockState state, LightColor color, Direction travel) {
		if (!accepts(state, color)) {
			return;
		}
		LAST_HIT.put(key(level, pos), level.getGameTime());
		if (!state.getValue(POWERED)) {
			level.setBlock(pos, state.setValue(POWERED, true), Block.UPDATE_ALL);
			level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.0F, 1.6F);
			level.sendParticles(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 1.0, pos.getZ() + 0.5, 6, 0.2, 0.1, 0.2, 0.02);
		}
		level.scheduleTick(pos, this, LightBeams.PULSE * 2 + 2);
	}

	@Override
	protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		Long last = LAST_HIT.get(key(level, pos));
		if (state.getValue(POWERED) && (last == null || level.getGameTime() - last > LightBeams.PULSE * 2)) {
			level.setBlock(pos, state.setValue(POWERED, false), Block.UPDATE_ALL);
			LAST_HIT.remove(key(level, pos));
		}
	}

	private static long key(ServerLevel level, BlockPos pos) {
		return pos.asLong() * 31 + level.dimension().identifier().hashCode();
	}

	@Override
	protected boolean isSignalSource(BlockState state) {
		return true;
	}

	@Override
	protected int getSignal(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
		return state.getValue(POWERED) ? 15 : 0;
	}

	@Override
	public BlockState rotateWithFork(BlockState state) {
		return state.cycle(COLOR).setValue(POWERED, false);
	}
}
