package dev.celestial.block.lore;

import dev.celestial.lore.Lore;
import dev.celestial.network.OpenLorePayload;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jspecify.annotations.Nullable;

/**
 * Скрижаль: каменная плита с высеченным листом Летописи (id в BE, тег `Sheet`). ПКМ открывает лист и показывает его в Кодексе. Неразрушима:
 * это часть постройки, а не добыча (лист можно читать сколько угодно, свиток же тратится).
 */
public class LoreTabletBlock extends BaseEntityBlock {
	public static final EnumProperty<Direction> FACING = BlockStateProperties.HORIZONTAL_FACING;
	private static final VoxelShape NS = Shapes.or(Block.box(3, 0, 6, 13, 2, 10), Block.box(4, 2, 7, 12, 15, 9));
	private static final VoxelShape EW = Shapes.or(Block.box(6, 0, 3, 10, 2, 13), Block.box(7, 2, 4, 9, 15, 12));

	public LoreTabletBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return state.getValue(FACING).getAxis() == Direction.Axis.Z ? NS : EW;
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}

	@Override
	public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new LoreTabletBlockEntity(pos, state);
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (player instanceof ServerPlayer sp && level.getBlockEntity(pos) instanceof LoreTabletBlockEntity tablet) {
			String id = tablet.sheet();
			if (Lore.sheet(id).isEmpty()) {
				sp.sendOverlayMessage(Component.translatable("lore.celestial.tablet.blank"));
				return InteractionResult.CONSUME;
			}
			if (!Lore.unlock(sp, id) && dev.celestial.data.CelestialData.get(sp).knowsLore(id)) {
				sp.sendOverlayMessage(Component.translatable("lore.celestial.scroll.known"));
			}
			ServerPlayNetworking.send(sp, new OpenLorePayload(id));
		}
		return InteractionResult.SUCCESS;
	}
}
