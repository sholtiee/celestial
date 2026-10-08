package dev.celestial.block.puzzle.memory;

import dev.celestial.puzzle.PuzzleZoneGuard;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Плита памяти: светится, когда алтарь показывает маршрут (SHOW) и когда на неё верно наступили (GOOD). После ошибки на миг
 * исчезает (GONE — без столкновения): игрок падает в неглубокую яму. Шаг засчитывается только ногами — стоя на земле,
 * не верхом и не в полёте на элитрах.
 */
public class MemoryPlateBlock extends Block {
	public enum Glow implements StringRepresentable {
		OFF, SHOW, GOOD, GONE;

		@Override
		public String getSerializedName() {
			return name().toLowerCase(java.util.Locale.ROOT);
		}
	}

	public static final EnumProperty<Glow> GLOW = EnumProperty.create("glow", Glow.class);

	public MemoryPlateBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(GLOW, Glow.OFF));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(GLOW);
	}

	@Override
	protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return state.getValue(GLOW) == Glow.GONE ? Shapes.empty() : super.getCollisionShape(state, level, pos, context);
	}

	@Override
	public void stepOn(Level level, BlockPos pos, BlockState state, Entity entity) {
		if (level instanceof ServerLevel server && entity instanceof ServerPlayer player && entity.onGround() && !player.isPassenger()
			&& !player.isFallFlying() && !player.isSpectator()) {
			for (var be : PuzzleZoneGuard.zones(server)) {
				if (be instanceof MemoryAltarBlockEntity altar && altar.owns(pos)) {
					altar.stepped(server, pos, player);
					break;
				}
			}
		}
		super.stepOn(level, pos, state, entity);
	}

	@Override
	protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		if (state.getValue(GLOW) == Glow.GONE || state.getValue(GLOW) == Glow.SHOW) {
			level.setBlock(pos, state.setValue(GLOW, Glow.OFF), Block.UPDATE_ALL);  // вернуться после провала или вспышки показа
		}
	}
}
