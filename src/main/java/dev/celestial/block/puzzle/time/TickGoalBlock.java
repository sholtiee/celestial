package dev.celestial.block.puzzle.time;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.InsideBlockEffectApplier;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Финиш «Хода маятника»: латунная плита-циферблат на полу (как нажимная). Встал на неё, дойдя по платформам, — загадка решена. */
public class TickGoalBlock extends Block implements dev.celestial.puzzle.PuzzleInteractive {
	private static final VoxelShape SHAPE = Block.box(1, 0, 1, 15, 1, 15);

	public TickGoalBlock(Properties properties) {
		super(properties);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	@Override
	protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return Shapes.empty();
	}

	@Override
	protected void entityInside(BlockState state, Level level, BlockPos pos, Entity entity, InsideBlockEffectApplier effectApplier, boolean isPrecise) {
		if (level instanceof ServerLevel server && entity instanceof Player player && level.getGameTime() % 5 == 0) {
			TickConductorBlockEntity conductor = TickConductorBlockEntity.find(server, pos);
			if (conductor != null) {
				conductor.reach(server, player);
			}
		}
	}
}
