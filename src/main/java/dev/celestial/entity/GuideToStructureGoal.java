package dev.celestial.entity;

import java.util.EnumSet;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.core.registries.Registries;
import dev.celestial.Celestial;

/** Светлячок замечает игрока и летит впереди него к ближайшей святыне Рая. */
public class GuideToStructureGoal extends Goal {
	public static final TagKey<Structure> GUIDE_TARGETS = TagKey.create(Registries.STRUCTURE, Celestial.id("wisp_guides_to"));
	private final LightWisp wisp;
	private Player follower;
	private BlockPos destination;
	private int recalc;

	public GuideToStructureGoal(LightWisp wisp) {
		this.wisp = wisp;
		this.setFlags(EnumSet.of(Goal.Flag.MOVE));
	}

	@Override
	public boolean canUse() {
		follower = wisp.level().getNearestPlayer(wisp, 10.0);
		return follower != null && !follower.isSpectator();
	}

	@Override
	public boolean canContinueToUse() {
		return follower != null && follower.isAlive() && wisp.distanceToSqr(follower) < 24 * 24;
	}

	@Override
	public void start() {
		recalc = 0;
		destination = null;
	}

	@Override
	public void tick() {
		if (--recalc <= 0) {
			recalc = 600;  // поиск постройки синхронный и догенерирует чанки — раз в 30 с, а не в 10
			if (wisp.level() instanceof ServerLevel level) {
				destination = level.findNearestMapStructure(GUIDE_TARGETS, wisp.blockPosition(), 24, false);
			}
		}
		if (destination == null) {
			return;
		}
		// держимся на 4-6 блоков впереди игрока по направлению к цели
		double dx = destination.getX() - follower.getX();
		double dz = destination.getZ() - follower.getZ();
		double len = Math.max(1.0, Math.sqrt(dx * dx + dz * dz));
		double lead = Math.min(6.0, len);
		wisp.getMoveControl().setWantedPosition(follower.getX() + dx / len * lead, follower.getEyeY() + 0.5, follower.getZ() + dz / len * lead, 1.4);
	}
}
