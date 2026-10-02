package dev.celestial.world.abyss;

import dev.celestial.data.CelestialData;
import dev.celestial.world.HeavenDimension;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.InsideBlockEffectApplier;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Portal;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.portal.TeleportTransition;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jspecify.annotations.Nullable;

/**
 * Разлом Бездны: чёрная воронка на дне Рая и ответная в Бездне. Шаг внутрь переносит между мирами.
 * Из Рая проход открыт только после Акта I (Серафим повержен) — до этого Разлом отталкивает.
 */
public class AbyssRiftBlock extends BaseEntityBlock implements Portal {
	private static final VoxelShape SHAPE = Block.column(16.0, 6.0, 12.0);

	public AbyssRiftBlock(Properties properties) {
		super(properties);
	}

	@Override
	public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new AbyssRiftBlockEntity(pos, state);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	@Override
	protected VoxelShape getEntityInsideCollisionShape(BlockState state, BlockGetter level, BlockPos pos, Entity entity) {
		return state.getShape(level, pos);
	}

	public static boolean sealed(Level level) {
		return level.dimension() == HeavenDimension.HEAVEN && level.getServer() != null && CelestialData.world(level.getServer()).act() < 1;
	}

	@Override
	protected void entityInside(BlockState state, Level level, BlockPos pos, Entity entity, InsideBlockEffectApplier effects, boolean precise) {
		if (!(entity instanceof ServerPlayer player) || !entity.canUsePortal(false)) {
			return;
		}
		if (sealed(level)) {
			if (!player.isOnPortalCooldown()) {
				player.sendOverlayMessage(Component.translatable("block.celestial.abyss_rift.sealed"));
				level.playSound(null, pos, SoundEvents.RESPAWN_ANCHOR_DEPLETE.value(), SoundSource.BLOCKS, 1.0F, 0.6F);
				player.setPortalCooldown(40);
			}
			player.setDeltaMovement(player.getDeltaMovement().x, 1.1, player.getDeltaMovement().z);
			player.needsSync = true;
			return;
		}
		entity.setAsInsidePortal(this, pos);
	}

	@Override
	public @Nullable TeleportTransition getPortalDestination(ServerLevel current, Entity entity, BlockPos entryPos) {
		boolean down = current.dimension() == HeavenDimension.HEAVEN;
		ServerLevel target = current.getServer().getLevel(down ? dev.celestial.world.dim.AbyssFeatures.ABYSS : HeavenDimension.HEAVEN);
		if (target == null) {
			return null;
		}
		BlockPos center = AbyssRifts.findOrCreate(target, entryPos, down);
		if (down && entity instanceof ServerPlayer player) {
			CelestialData.update(player, d -> d.withCodex("place:abyss"));
			player.sendSystemMessage(Component.translatable("story.celestial.abyss_enter"));
		}
		Vec3 arrival = Vec3.atBottomCenterOf(center.offset(0, 1, 3));
		return new TeleportTransition(target, arrival, Vec3.ZERO, 180.0F, 0.0F,
			TeleportTransition.PLAY_PORTAL_SOUND.then(TeleportTransition.PLACE_PORTAL_TICKET));
	}

	@Override
	public Portal.Transition getLocalTransition() {
		return Portal.Transition.CONFUSION;
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		if (random.nextInt(3) == 0) {
			level.addParticle(ParticleTypes.REVERSE_PORTAL, pos.getX() + random.nextDouble(), pos.getY() + 0.8, pos.getZ() + random.nextDouble(),
				0, -0.05, 0);
		}
		level.addParticle(ParticleTypes.SMOKE, pos.getX() + random.nextDouble(), pos.getY() + 0.8, pos.getZ() + random.nextDouble(), 0, 0, 0);
	}

	@Override
	protected ItemStack getCloneItemStack(LevelReader level, BlockPos pos, BlockState state, boolean includeData) {
		return ItemStack.EMPTY;
	}

	@Override
	protected boolean canBeReplaced(BlockState state, Fluid fluid) {
		return false;
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.INVISIBLE;
	}
}
