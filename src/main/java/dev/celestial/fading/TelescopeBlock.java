package dev.celestial.fading;

import dev.celestial.Celestial;
import dev.celestial.data.CelestialData;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jspecify.annotations.Nullable;

/**
 * Телескоп — рабочее место Звездочёта. Ночью показывает стадию Угасания и направление к ближайшей
 * Звёздной обсерватории (в Верхнем мире), днём звёзд не видно.
 */
public class TelescopeBlock extends HorizontalDirectionalBlock {
	private static final TagKey<Structure> OBSERVATORIES = TagKey.create(Registries.STRUCTURE, Celestial.id("observatories"));
	private static final VoxelShape SHAPE = Block.box(2, 0, 2, 14, 16, 14);

	public TelescopeBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING);
	}

	@Override
	public @Nullable BlockState getStateForPlacement(BlockPlaceContext context) {
		return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!(level instanceof ServerLevel server)) {
			return InteractionResult.SUCCESS;
		}
		if (!level.canSeeSky(pos.above()) || level.isBrightOutside() && level.dimension() == Level.OVERWORLD) {
			player.sendOverlayMessage(Component.translatable("block.celestial.telescope.no_stars"));
			return InteractionResult.SUCCESS;
		}
		CelestialData.update(player, d -> d.withCodex("place:telescope"));
		observe(server, pos, player);
		int stage = Fading.stage(server.getServer());
		player.sendSystemMessage(Component.translatable("block.celestial.telescope.stage." + stage));
		if (level.dimension() == Level.OVERWORLD) {
			BlockPos found = server.findNearestMapStructure(OBSERVATORIES, pos, 64, false);
			if (found != null) {
				int dist = Mth.floor(Math.sqrt(found.distSqr(pos)));
				player.sendSystemMessage(Component.translatable("block.celestial.telescope.observatory",
					Component.translatable("direction.celestial." + direction(pos, found)), dist));
			}
		}
		return InteractionResult.SUCCESS;
	}

	/**
	 * Созвездие хора, видимое в эту ночь: вне Астрала — по фазе Луны (8 хоров), в Астрале — Серафимы. Первое наблюдение — запись
	 * {@code constellation:<хор>} в Кодексе (рисунок во вкладке «Созвездия»).
	 */
	private static void observe(ServerLevel level, BlockPos pos, Player player) {
		dev.celestial.astral.Choir choir = level.dimension() == dev.celestial.world.dim.AbyssFeatures.ASTRAL ? dev.celestial.astral.Choir.SERAPHIM
			: dev.celestial.astral.Choir.forMoonPhase(level.environmentAttributes().getValue(
				net.minecraft.world.attribute.EnvironmentAttributes.MOON_PHASE, net.minecraft.world.phys.Vec3.atCenterOf(pos)).index());
		if (choir == null) {
			return;
		}
		boolean fresh = !CelestialData.get(player).knows("constellation:" + choir.id);
		CelestialData.update(player, d -> d.withCodex("constellation:" + choir.id));
		player.sendSystemMessage(Component.translatable(fresh ? "block.celestial.telescope.constellation_new" : "block.celestial.telescope.constellation",
			Component.translatable("choir.celestial." + choir.id).withStyle(net.minecraft.ChatFormatting.AQUA)));
		if (fresh) {
			level.sendParticles(dev.celestial.registry.ModParticles.STARLIGHT, pos.getX() + 0.5, pos.getY() + 1.4, pos.getZ() + 0.5, 25, 0.4, 0.4, 0.4, 0.03);
		}
	}

	/** Сторона света: n, ne, e, se, s, sw, w, nw. */
	static String direction(BlockPos from, BlockPos to) {
		double angle = Math.toDegrees(Math.atan2(to.getX() - from.getX(), from.getZ() - to.getZ()));
		String[] names = {"n", "ne", "e", "se", "s", "sw", "w", "nw"};
		return names[Math.floorMod((int) Math.round(angle / 45.0), 8)];
	}
}
