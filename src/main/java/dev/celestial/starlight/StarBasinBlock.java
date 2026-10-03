package dev.celestial.starlight;

import dev.celestial.registry.ModItems;
import java.util.Map;
import java.util.function.Supplier;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.InsideBlockEffectApplier;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.BooleanOp;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Звёздная купель: в неё выливают Флаконы звёздного света (уровень 0–3), а брошенные внутрь предметы
 * превращаются: железо → звёздная сталь, небесный кристалл → заряженный кристалл, сгусток тьмы → звёздный обломок.
 * Одно деление превращает целую стопку (до 16 штук).
 */
public class StarBasinBlock extends Block {
	public static final IntegerProperty LEVEL = IntegerProperty.create("level", 0, 3);
	private static final VoxelShape SHAPE = Shapes.join(Block.box(1, 0, 1, 15, 12, 15), Block.box(3, 4, 3, 13, 12, 13), BooleanOp.ONLY_FIRST);
	private static final Map<Item, Supplier<Item>> TRANSFORMS = Map.of(
		Items.IRON_INGOT, () -> ModItems.STARSTEEL_INGOT,
		dev.celestial.registry.ModBlocks.SKY_CRYSTAL.asItem(), () -> ModItems.CHARGED_CRYSTAL,
		ModItems.SHADOW_ESSENCE, () -> ModItems.STAR_FRAGMENT);

	public StarBasinBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(LEVEL, 0));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(LEVEL);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand,
		BlockHitResult hit) {
		if (!stack.is(ModItems.STARLIGHT_FLASK)) {
			return InteractionResult.TRY_WITH_EMPTY_HAND;
		}
		int current = state.getValue(LEVEL);
		if (current >= 3) {
			return InteractionResult.PASS;
		}
		if (!level.isClientSide()) {
			stack.consume(1, player);
			ItemStack bottle = new ItemStack(Items.GLASS_BOTTLE);
			if (!player.getInventory().add(bottle)) {
				player.spawnAtLocation((net.minecraft.server.level.ServerLevel) level, bottle);
			}
			level.setBlock(pos, state.setValue(LEVEL, current + 1), Block.UPDATE_ALL);
			level.playSound(null, pos, SoundEvents.BOTTLE_EMPTY, SoundSource.BLOCKS, 1.0F, 1.2F);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	protected void entityInside(BlockState state, Level level, BlockPos pos, Entity entity, InsideBlockEffectApplier effects, boolean precise) {
		if (!(level instanceof ServerLevel server) || !(entity instanceof ItemEntity item) || state.getValue(LEVEL) == 0 || item.tickCount < 10) {
			return;
		}
		Supplier<Item> result = TRANSFORMS.get(item.getItem().getItem());
		if (result == null) {
			return;
		}
		int count = Math.min(16, item.getItem().getCount());
		item.getItem().shrink(count);
		if (item.getItem().isEmpty()) {
			item.discard();
		}
		ItemEntity out = new ItemEntity(server, pos.getX() + 0.5, pos.getY() + 1.0, pos.getZ() + 0.5, new ItemStack(result.get(), count));
		out.setDeltaMovement(0, 0.25, 0);
		server.addFreshEntity(out);
		server.setBlock(pos, state.setValue(LEVEL, state.getValue(LEVEL) - 1), Block.UPDATE_ALL);
		server.sendParticles(dev.celestial.registry.ModParticles.STARLIGHT, pos.getX() + 0.5, pos.getY() + 0.9, pos.getZ() + 0.5, 40, 0.3, 0.2, 0.3, 0.12);
		server.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 1.2F, 1.4F);
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		if (state.getValue(LEVEL) > 0 && random.nextInt(3) == 0) {
			level.addParticle(dev.celestial.registry.ModParticles.STARLIGHT, pos.getX() + 0.3 + random.nextDouble() * 0.4, pos.getY() + 0.8,
				pos.getZ() + 0.3 + random.nextDouble() * 0.4, 0, 0.03, 0);
		}
	}
}
