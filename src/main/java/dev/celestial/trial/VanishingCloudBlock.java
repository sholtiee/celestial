package dev.celestial.trial;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Исчезающее облако: через ~1,5 с после того как на него встали, тает, а через 5 с возвращается. */
public class VanishingCloudBlock extends Block {
	public static final BooleanProperty VANISHED = BooleanProperty.create("vanished");

	public VanishingCloudBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(VANISHED, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(VANISHED);
	}

	@Override
	public void stepOn(Level level, BlockPos pos, BlockState state, Entity entity) {
		if (!level.isClientSide() && !state.getValue(VANISHED) && !level.getBlockTicks().hasScheduledTick(pos, this)) {
			level.scheduleTick(pos, this, 30);
		}
	}

	@Override
	protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		boolean vanish = !state.getValue(VANISHED);
		level.setBlock(pos, state.setValue(VANISHED, vanish), Block.UPDATE_ALL);
		level.sendParticles(ParticleTypes.CLOUD, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 8, 0.3, 0.3, 0.3, 0.02);
		level.playSound(null, pos, SoundEvents.WOOL_BREAK, SoundSource.BLOCKS, 0.6F, vanish ? 1.4F : 0.8F);
		if (vanish) {
			level.scheduleTick(pos, this, 100);
		}
	}

	@Override
	protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return state.getValue(VANISHED) ? Shapes.empty() : Shapes.block();
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return state.getValue(VANISHED) ? Shapes.empty() : Shapes.block();
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return state.getValue(VANISHED) ? RenderShape.INVISIBLE : RenderShape.MODEL;
	}
}
