package dev.celestial.block.puzzle.echo;

import dev.celestial.puzzle.PuzzleZoneGuard;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Камень-резонатор «Эха во тьме»: ПКМ — прислушаться (эхо приходит с задержкой ∝ расстоянию до скрытого ядра),
 * ЛКМ — ударить (засчитать в порядок). На свету камень молчит. Неразрушим. STRUCK — уже ударен в текущей попытке.
 */
public class EchoStoneBlock extends Block implements dev.celestial.puzzle.PuzzleInteractive {
	public static final BooleanProperty STRUCK = BooleanProperty.create("struck");

	public EchoStoneBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(STRUCK, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(STRUCK);
	}

	private static EchoAltarBlockEntity altar(ServerLevel level, BlockPos pos) {
		for (var be : PuzzleZoneGuard.zones(level)) {
			if (be instanceof EchoAltarBlockEntity altar && altar.owns(level, pos)) {
				return altar;
			}
		}
		return null;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (level instanceof ServerLevel server) {
			EchoAltarBlockEntity altar = altar(server, pos);
			if (altar != null) {
				altar.listen(server, pos, player);
			}
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	protected void attack(BlockState state, Level level, BlockPos pos, Player player) {
		if (level instanceof ServerLevel server) {
			EchoAltarBlockEntity altar = altar(server, pos);
			if (altar != null) {
				altar.strike(server, pos, player);
			}
		}
	}
}
