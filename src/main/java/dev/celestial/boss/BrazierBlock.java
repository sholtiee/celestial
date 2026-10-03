package dev.celestial.boss;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Жаровня Логова: зажигается огнивом, огненным зарядом, Флаконом звёздного света или факелом в руке.
 * Пока на арене горит хотя бы две жаровни, Пожиратель Света уязвим — и он старается их погасить.
 */
public class BrazierBlock extends Block {
	public static final BooleanProperty LIT = BooleanProperty.create("lit");
	private static final VoxelShape SHAPE = Block.box(2, 0, 2, 14, 14, 14);

	public BrazierBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(LIT, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(LIT);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	public static boolean canIgnite(ItemStack stack) {
		return stack.is(Items.FLINT_AND_STEEL) || stack.is(Items.FIRE_CHARGE) || stack.is(dev.celestial.registry.ModItems.STARLIGHT_FLASK)
			|| stack.is(dev.celestial.world.abyss.Darkness.LIGHT_SOURCES);
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand,
		BlockHitResult hit) {
		if (state.getValue(LIT) || !canIgnite(stack)) {
			return InteractionResult.TRY_WITH_EMPTY_HAND;
		}
		if (level instanceof ServerLevel server) {
			ignite(server, pos, state);
			if (stack.is(Items.FLINT_AND_STEEL)) {
				stack.hurtAndBreak(1, player, hand == InteractionHand.MAIN_HAND
					? net.minecraft.world.entity.EquipmentSlot.MAINHAND : net.minecraft.world.entity.EquipmentSlot.OFFHAND);
			} else if (stack.is(Items.FIRE_CHARGE)) {
				stack.consume(1, player);
			}
		}
		return InteractionResult.SUCCESS;
	}

	public static void ignite(ServerLevel level, BlockPos pos, BlockState state) {
		level.setBlock(pos, state.setValue(LIT, true), Block.UPDATE_ALL);
		level.playSound(null, pos, SoundEvents.BLAZE_SHOOT, SoundSource.BLOCKS, 1.0F, 1.4F);
		level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, pos.getX() + 0.5, pos.getY() + 1.0, pos.getZ() + 0.5, 30, 0.25, 0.4, 0.25, 0.03);
	}

	public static void extinguish(ServerLevel level, BlockPos pos, BlockState state) {
		level.setBlock(pos, state.setValue(LIT, false), Block.UPDATE_ALL);
		level.playSound(null, pos, SoundEvents.FIRE_EXTINGUISH, SoundSource.BLOCKS, 1.5F, 0.6F);
		level.sendParticles(ParticleTypes.LARGE_SMOKE, pos.getX() + 0.5, pos.getY() + 1.0, pos.getZ() + 0.5, 30, 0.3, 0.4, 0.3, 0.02);
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		if (state.getValue(LIT)) {
			level.addParticle(ParticleTypes.SOUL_FIRE_FLAME, pos.getX() + 0.3 + random.nextDouble() * 0.4, pos.getY() + 0.95,
				pos.getZ() + 0.3 + random.nextDouble() * 0.4, 0, 0.04, 0);
			if (random.nextInt(4) == 0) {
				level.addParticle(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5, 0, 0.05, 0);
			}
		}
	}
}
