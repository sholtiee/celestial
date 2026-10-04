package dev.celestial.block.light;

import dev.celestial.light.BeamTarget;
import dev.celestial.light.LightBeams;
import dev.celestial.light.LightColor;
import dev.celestial.registry.ModBlockEntities;
import dev.celestial.world.HeavenDimension;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Источник луча. Солнечная линза светит днём под открытым небом (в Раю — всегда),
 * Световой фонарь — пока на него подан сигнал красного камня.
 */
public class BeamSourceBlock extends Block implements EntityBlock, Rotatable {
	public static final EnumProperty<Direction> FACING = BlockStateProperties.FACING;
	public static final BooleanProperty ACTIVE = BooleanProperty.create("active");
	/** Источник святилища (только из генерации): его луч единственный, что засчитывается запечатанным приёмникам; не ломается. */
	public static final BooleanProperty SEALED = BooleanProperty.create("sealed");

	public enum Kind { SUN_LENS, LANTERN }

	private final Kind kind;

	public BeamSourceBlock(Kind kind, Properties properties) {
		super(properties);
		this.kind = kind;
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(ACTIVE, false).setValue(SEALED, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING, ACTIVE, SEALED);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		return defaultBlockState().setValue(FACING, context.getNearestLookingDirection().getOpposite());
	}

	@Override
	public BlockState rotateWithFork(BlockState state) {
		Direction[] all = Direction.values();
		return state.setValue(FACING, all[(state.getValue(FACING).ordinal() + 1) % all.length]);
	}

	public boolean shouldShine(Level level, BlockPos pos) {
		return switch (kind) {
			case SUN_LENS -> HeavenDimension.isHeaven(level) || (level.isBrightOutside() && level.canSeeSky(pos.above()));
			case LANTERN -> level.hasNeighborSignal(pos);
		};
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new BeamSourceBlockEntity(pos, state);
	}

	@Override
	@SuppressWarnings("unchecked")
	public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		return level.isClientSide() || type != ModBlockEntities.BEAM_SOURCE ? null
			: (BlockEntityTicker<T>) (BlockEntityTicker<BeamSourceBlockEntity>) BeamSourceBlock::serverTick;
	}

	private static void serverTick(Level level, BlockPos pos, BlockState state, BeamSourceBlockEntity be) {
		if (level.getGameTime() % LightBeams.PULSE != Math.floorMod(pos.asLong(), LightBeams.PULSE) || !(level instanceof ServerLevel server)
			|| !(state.getBlock() instanceof BeamSourceBlock source)) {
			return;
		}
		boolean shine = source.shouldShine(level, pos);
		if (shine != state.getValue(ACTIVE)) {
			level.setBlock(pos, state.setValue(ACTIVE, shine), Block.UPDATE_CLIENTS);
		}
		if (!shine) {
			return;
		}
		LightBeams.sealedSource = state.getValue(SEALED);
		try {
			LightBeams.trace(level, pos, state.getValue(FACING), LightColor.WHITE, new LightBeams.Visitor() {
				@Override
				public void hit(BlockPos hitPos, BlockState hitState, LightColor color, Direction travel) {
					if (hitState.getBlock() instanceof BeamTarget target) {
						target.onBeamHit(server, hitPos, hitState, color, travel);
					}
				}
			});
		} finally {
			LightBeams.sealedSource = false;
		}
	}

	@Override
	protected float getDestroyProgress(BlockState state, net.minecraft.world.entity.player.Player player, net.minecraft.world.level.BlockGetter level, BlockPos pos) {
		return state.getValue(SEALED) ? 0.0F : super.getDestroyProgress(state, player, level, pos);
	}

	/** Клиент: рисуем луч частицами пыли нужного цвета вдоль всего пути. */
	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		if (!state.getValue(ACTIVE)) {
			return;
		}
		LightBeams.trace(level, pos, state.getValue(FACING), LightColor.WHITE, new LightBeams.Visitor() {
			@Override
			public void segment(LightBeams.Segment s) {
				DustParticleOptions dust = new DustParticleOptions(s.color().rgb, 0.8F);
				for (int i = 0; i < Math.max(2, s.length() * 2); i++) {
					double t = random.nextDouble() * (s.length() + 0.5);
					Vec3 p = Vec3.atCenterOf(s.start()).add(Vec3.atLowerCornerOf(s.dir().getUnitVec3i()).scale(t + 0.5));
					level.addParticle(dust, p.x, p.y, p.z, 0, 0, 0);
				}
			}
		});
	}
}
