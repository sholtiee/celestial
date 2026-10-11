package dev.celestial.astral;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.BlockHitResult;
import org.jspecify.annotations.Nullable;

/**
 * Звёздный диск хора — центр поля 5×5 из гнёзд (на одной высоте с ним). Хор задаёт NBT {@code Choir} сущности блока.
 * Вставь Звёздные камни в гнёзда по рисунку созвездия (верх рисунка в Кодексе — север): когда камней столько же, сколько звёзд,
 * диск сверяет — верно: хор собран (мост света — печати рядом растворяются, благословение); неверно — камни выпрыгивают, блокировка.
 * ПКМ по собранному диску пустой рукой — сделать хор покровителем.
 */
public class StarDiskBlock extends BaseEntityBlock implements dev.celestial.puzzle.PuzzleInteractive {
	public static final BooleanProperty LIT = BooleanProperty.create("lit");

	public StarDiskBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(LIT, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(LIT);
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (level instanceof ServerLevel server && player instanceof ServerPlayer sp && level.getBlockEntity(pos) instanceof StarDiskBlockEntity disk) {
			Choir choir = disk.choir();
			if (choir == null) {
				return InteractionResult.PASS;
			}
			if (!disk.solved()) {
				sp.sendOverlayMessage(Component.translatable("block.celestial.star_disk.hint", Component.translatable("choir.celestial." + choir.id),
					choir.points.length - 1));
			} else if (Choirs.setPatron(sp, choir)) {
				sp.sendSystemMessage(Component.translatable("choir.celestial.patron_set", Component.translatable("choir.celestial." + choir.id),
					Component.translatable("choir.celestial." + choir.id + ".blessing")));
				server.sendParticles(dev.celestial.registry.ModParticles.STARLIGHT, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5, 30, 0.6, 0.6, 0.6, 0.05);
			}
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new StarDiskBlockEntity(pos, state);
	}
}
