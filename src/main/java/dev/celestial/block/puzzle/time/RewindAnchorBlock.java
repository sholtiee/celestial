package dev.celestial.block.puzzle.time;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.BlockHitResult;

/** Якорь «Комнаты-перемотки»: ПКМ (в выживании) — зажечь. Перемотка гасит. Все якоря разом — загадка решена. Неразрушим. */
public class RewindAnchorBlock extends Block implements dev.celestial.puzzle.PuzzleInteractive {
	public static final BooleanProperty LIT = BooleanProperty.create("lit");

	public RewindAnchorBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(LIT, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(LIT);
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!(level instanceof ServerLevel server) || player.isSpectator()) {
			return InteractionResult.SUCCESS;
		}
		RewindCoreBlockEntity core = RewindCoreBlockEntity.find(server, pos);
		if (core == null || state.getValue(LIT)) {
			return InteractionResult.SUCCESS;
		}
		if (core.solved()) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.rewind_room.solved"));
			return InteractionResult.SUCCESS;
		}
		level.setBlock(pos, state.setValue(LIT, true), Block.UPDATE_ALL);
		level.playSound(null, pos, SoundEvents.RESPAWN_ANCHOR_CHARGE, SoundSource.BLOCKS, 1.0F, 1.3F);
		server.sendParticles(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 1.1, pos.getZ() + 0.5, 12, 0.3, 0.3, 0.3, 0.03);
		core.anchorLit(server, player);
		return InteractionResult.SUCCESS;
	}
}
