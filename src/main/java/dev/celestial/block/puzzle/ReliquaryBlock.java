package dev.celestial.block.puzzle;

import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import org.jspecify.annotations.Nullable;

/**
 * Реликварий — награда за решённую загадку. В отличие от сундука его нельзя сломать, сдвинуть, взорвать и вытянуть воронкой
 * (это не контейнер), а открывается он, только когда рядом не осталось ни одной Печати-двери. Прокопать стену к сокровищу бессмысленно.
 */
public class ReliquaryBlock extends BaseEntityBlock {
	/** Печать считается держащей сокровище, если она ближе этого расстояния. */
	public static final int SEAL_RANGE = 8;

	public ReliquaryBlock(Properties properties) {
		super(properties);
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new ReliquaryBlockEntity(pos, state);
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}

	public static boolean sealed(Level level, BlockPos pos) {
		for (BlockPos p : BlockPos.betweenClosed(pos.offset(-SEAL_RANGE, -SEAL_RANGE / 2, -SEAL_RANGE), pos.offset(SEAL_RANGE, SEAL_RANGE / 2, SEAL_RANGE))) {
			if (level.getBlockState(p).is(ModBlocks.SEALED_DOOR)) {
				return true;
			}
		}
		return false;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (level instanceof ServerLevel server && level.getBlockEntity(pos) instanceof ReliquaryBlockEntity be) {
			if (sealed(level, pos)) {
				player.sendOverlayMessage(Component.translatable("puzzle.celestial.reliquary.sealed"));
				return InteractionResult.CONSUME;
			}
			be.claim(server, player);
		}
		return InteractionResult.SUCCESS;
	}
}
