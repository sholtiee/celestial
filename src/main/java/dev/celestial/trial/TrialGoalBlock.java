package dev.celestial.trial;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Финишный кристалл: встал на него — испытание на время засчитано (ищет контроллер в радиусе 32). */
public class TrialGoalBlock extends Block {
	public TrialGoalBlock(Properties properties) {
		super(properties);
	}

	@Override
	public void stepOn(Level level, BlockPos pos, BlockState state, Entity entity) {
		if (level instanceof ServerLevel server && entity instanceof Player player && level.getGameTime() % 5 == 0) {
			for (BlockPos p : BlockPos.betweenClosed(pos.offset(-32, -12, -32), pos.offset(32, 12, 32))) {
				BlockEntity be = level.getBlockEntity(p);
				if (be instanceof TrialControllerBlockEntity trial && trial.isRunning()) {
					trial.reachGoal(server, player);
					return;
				}
			}
		}
		super.stepOn(level, pos, state, entity);
	}
}
