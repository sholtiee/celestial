package dev.celestial.block.puzzle;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Небесный колокол: 5 нот. Звон слышит ближайший колокольный алтарь (загадка «повтори мелодию»). */
public class SkyBellBlock extends Block {
	public static final IntegerProperty NOTE = IntegerProperty.create("note", 0, 4);
	public static final float[] PITCH = {0.7F, 0.84F, 1.0F, 1.19F, 1.41F};
	private static final VoxelShape SHAPE = Block.box(3, 2, 3, 13, 15, 13);

	public SkyBellBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(NOTE, 0));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(NOTE);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	public static void ring(ServerLevel level, BlockPos pos, int note) {
		level.playSound(null, pos, SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.BLOCKS, 1.5F, PITCH[note]);
		level.sendParticles(ParticleTypes.NOTE, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5, 1, 0, 0, 0, note / 24.0);
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (level instanceof ServerLevel server) {
			int note = state.getValue(NOTE);
			ring(server, pos, note);
			// сообщаем ближайшему алтарю в радиусе 12 блоков
			for (BlockPos p : BlockPos.betweenClosed(pos.offset(-12, -6, -12), pos.offset(12, 6, 12))) {
				BlockEntity be = level.getBlockEntity(p);
				if (be instanceof BellAltarBlockEntity altar) {
					altar.onBellRung(server, note, player);
					break;
				}
			}
		}
		return InteractionResult.SUCCESS;
	}
}
