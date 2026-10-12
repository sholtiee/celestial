package dev.celestial.block.puzzle.time;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Платформа такта: то твёрдая латунная плита, то призрачный контур, сквозь который падаешь. Такт задаёт дирижёр зала
 * ({@link TickConductorBlockEntity}); {@code phase} 0..3 — сдвиг на четверть такта, так по платформам бежит «волна».
 */
public class TickPlatformBlock extends Block {
	public static final BooleanProperty SOLID = BooleanProperty.create("solid");
	public static final IntegerProperty PHASE = IntegerProperty.create("phase", 0, 3);
	private static final VoxelShape SLAB = Block.box(0, 8, 0, 16, 16, 16);

	public TickPlatformBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(SOLID, true).setValue(PHASE, 0));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(SOLID, PHASE);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SLAB;
	}

	@Override
	protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return state.getValue(SOLID) ? SLAB : Shapes.empty();
	}
}
