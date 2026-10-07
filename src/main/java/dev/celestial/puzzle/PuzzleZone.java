package dev.celestial.puzzle;

import net.minecraft.core.BlockPos;

/**
 * Сущность блока, которая охраняет объём своей загадки, пока та не решена: внутри нельзя ставить блоки и лить жидкости
 * ({@link PuzzleZoneGuard}). Иначе свой блок-стопор на льду или своё зеркало в лабиринте заменяли решение.
 */
public interface PuzzleZone {
	/** Загадка ещё не решена и позиция внутри её охраняемого объёма. */
	boolean guards(BlockPos pos);
}
