package dev.celestial.block.machine;

import dev.celestial.light.BeamTarget;
import dev.celestial.light.LightBeams;
import dev.celestial.light.LightColor;
import dev.celestial.registry.ModBlockEntities;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.redstone.Orientation;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Облачный лифт: пока он работает (на него падает луч или подан сигнал красного камня),
 * поднимает всех, кто стоит в столбе над ним (до 12 блоков). Присесть — плавно спуститься.
 */
public class CloudLiftBlock extends Block implements EntityBlock, BeamTarget {
	public static final BooleanProperty LIT = BooleanProperty.create("lit");
	private static final int HEIGHT = 12;
	private static final Map<Long, Long> LAST_BEAM = new ConcurrentHashMap<>();

	public static void clearState() {
		LAST_BEAM.clear();
	}

	public CloudLiftBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(LIT, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(LIT);
	}

	@Override
	public void onBeamHit(ServerLevel level, BlockPos pos, BlockState state, LightColor color, Direction travel) {
		LAST_BEAM.put(pos.asLong(), level.getGameTime());
		update(level, pos, state);
	}

	@Override
	protected void neighborChanged(BlockState state, Level level, BlockPos pos, Block block, @Nullable Orientation orientation, boolean moved) {
		if (level instanceof ServerLevel server) {
			update(server, pos, state);
		}
	}

	private void update(ServerLevel level, BlockPos pos, BlockState state) {
		Long beam = LAST_BEAM.get(pos.asLong());
		boolean on = level.hasNeighborSignal(pos) || (beam != null && level.getGameTime() - beam <= LightBeams.PULSE * 2);
		if (on != state.getValue(LIT)) {
			level.setBlock(pos, state.setValue(LIT, on), Block.UPDATE_ALL);
		}
		if (on) {
			level.scheduleTick(pos, this, LightBeams.PULSE * 2 + 2);
		}
	}

	@Override
	protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		update(level, pos, state);
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new CloudLiftBlockEntity(pos, state);
	}

	@Override
	@SuppressWarnings("unchecked")
	public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		// работает и на клиенте: свой игрок двигается на стороне клиента
		return !state.getValue(LIT) || type != ModBlockEntities.CLOUD_LIFT ? null
			: (BlockEntityTicker<T>) (BlockEntityTicker<CloudLiftBlockEntity>) (l, p, s, be) -> lift(l, p);
	}

	private static void lift(Level level, BlockPos pos) {
		AABB column = new AABB(pos.getX(), pos.getY() + 1, pos.getZ(), pos.getX() + 1, pos.getY() + 1 + HEIGHT, pos.getZ() + 1);
		for (Entity e : level.getEntities((Entity) null, column, e -> e instanceof LivingEntity || e instanceof net.minecraft.world.entity.item.ItemEntity)) {
			Vec3 m = e.getDeltaMovement();
			double vy = e.isShiftKeyDown() ? Math.max(m.y, -0.12) : Math.min(m.y + 0.12, 0.45);
			e.setDeltaMovement(m.x * 0.9, vy, m.z * 0.9);
			e.resetFallDistance();
		}
		if (level.isClientSide() && level.getRandom().nextInt(3) == 0) {
			level.addParticle(ParticleTypes.CLOUD, pos.getX() + level.getRandom().nextDouble(), pos.getY() + 1.1,
				pos.getZ() + level.getRandom().nextDouble(), 0, 0.15, 0);
		}
	}
}
