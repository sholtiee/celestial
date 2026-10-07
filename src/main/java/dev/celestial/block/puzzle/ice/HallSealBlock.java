package dev.celestial.block.puzzle.ice;

import dev.celestial.block.puzzle.SealedDoorBlock;
import dev.celestial.puzzle.PuzzleZoneGuard;
import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModBlocks;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import org.jspecify.annotations.Nullable;

/**
 * Печать трёх залов (Ледяная цитадель): горит руной за каждый решённый зал скользящего льда в цитадели. Когда решены все,
 * растворяет печать-двери рядом с собой — путь к арене Архонта. Неразрушима; залы берёт из реестра загруженных зон загадок
 * (раз в 2 с, без сканирования мира).
 */
public class HallSealBlock extends BaseEntityBlock implements dev.celestial.puzzle.PuzzleInteractive {
	public static final IntegerProperty LIT = IntegerProperty.create("lit", 0, 3);
	public static final BooleanProperty OPEN = BooleanProperty.create("open");
	private static final int RANGE = 48;
	private static final int DOOR_RANGE = 5;

	public HallSealBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(LIT, 0).setValue(OPEN, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(LIT, OPEN);
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new Entity(pos, state);
	}

	@Override
	public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		return level.isClientSide() || state.getValue(OPEN) ? null : createTickerHelper(type, ModBlockEntities.HALL_SEAL, HallSealBlock::serverTick);
	}

	/** Залы вокруг: [решено, всего]. */
	private static int[] count(ServerLevel level, BlockPos pos) {
		int solved = 0, total = 0;
		for (BlockEntity be : PuzzleZoneGuard.zones(level)) {
			if (be instanceof GlacierHallBlockEntity hall && Math.abs(be.getBlockPos().getX() - pos.getX()) <= RANGE
				&& Math.abs(be.getBlockPos().getZ() - pos.getZ()) <= RANGE && Math.abs(be.getBlockPos().getY() - pos.getY()) <= 8) {
				total++;
				if (hall.solved()) {
					solved++;
				}
			}
		}
		return new int[] {solved, total};
	}

	private static void serverTick(Level level, BlockPos pos, BlockState state, Entity be) {
		if (level.getGameTime() % 40 != 0 || !(level instanceof ServerLevel server)) {
			return;
		}
		int[] c = count(server, pos);
		int lit = Math.min(3, c[0]);
		if (lit != state.getValue(LIT)) {
			state = state.setValue(LIT, lit);
			level.setBlock(pos, state, Block.UPDATE_ALL);
			level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 2.0F, 0.6F + lit * 0.2F);
		}
		if (c[1] >= be.required && c[0] >= c[1]) {  // все залы загружены и решены (required — сколько их в постройке)
			for (BlockPos d : BlockPos.betweenClosed(pos.offset(-DOOR_RANGE, -2, -DOOR_RANGE), pos.offset(DOOR_RANGE, 6, DOOR_RANGE))) {
				if (level.getBlockState(d).is(ModBlocks.SEALED_DOOR)) {
					SealedDoorBlock.dissolve(server, d.immutable());
				}
			}
			level.setBlock(pos, state.setValue(OPEN, true), Block.UPDATE_ALL);
			server.playSound(null, pos, SoundEvents.BEACON_POWER_SELECT, SoundSource.BLOCKS, 3.0F, 0.5F);
			server.sendParticles(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 1.5, pos.getZ() + 0.5, 60, 1.0, 1.5, 1.0, 0.1);
			for (Player player : server.getEntitiesOfClass(Player.class, new AABB(pos).inflate(40))) {
				player.sendSystemMessage(Component.translatable("puzzle.celestial.hall_seal.open").withStyle(ChatFormatting.AQUA));
			}
		}
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (level instanceof ServerLevel server) {
			if (state.getValue(OPEN)) {
				player.sendOverlayMessage(Component.translatable("puzzle.celestial.hall_seal.open"));
			} else {
				int[] c = count(server, pos);
				player.sendOverlayMessage(Component.translatable("puzzle.celestial.hall_seal.status", c[0], c[1]));
			}
		}
		return InteractionResult.SUCCESS;
	}

	/** Сущность нужна только ради тикера (печать ставится генерацией мира, где запланированные тики не ставятся). */
	public static class Entity extends BlockEntity {
		private int required = 1;

		public Entity(BlockPos pos, BlockState state) {
			super(ModBlockEntities.HALL_SEAL, pos, state);
		}

		@Override
		protected void saveAdditional(net.minecraft.world.level.storage.ValueOutput output) {
			super.saveAdditional(output);
			output.putInt("Halls", required);
		}

		@Override
		protected void loadAdditional(net.minecraft.world.level.storage.ValueInput input) {
			super.loadAdditional(input);
			required = Math.max(1, input.getIntOr("Halls", 1));
		}
	}
}
