package dev.celestial.block.eden;

import dev.celestial.data.CelestialData;
import dev.celestial.eden.Exile;
import dev.celestial.lore.Lore;
import dev.celestial.registry.ModEffects;
import dev.celestial.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
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
 * Плод Сада Начала. Жизни: полное лечение, сытость, Благодать +2 (закрыт для «изгнанных»). Познания: много опыта и Благодать +1, открывает лист «Плод»,
 * но вешает «Изгнание» (лист смоковницы в инвентаре принимает удар на себя). Съеденный плод созревает снова через игровую неделю (отложенный тик).
 */
public class FruitBlock extends Block {
	public static final BooleanProperty RIPE = BooleanProperty.create("ripe");
	public static final int REGROW_TICKS = 7 * 24000;
	private static final VoxelShape SHAPE = Block.box(4, 2, 4, 12, 16, 12);
	private final boolean life;

	public FruitBlock(Properties properties, boolean life) {
		super(properties);
		this.life = life;
		registerDefaultState(stateDefinition.any().setValue(RIPE, true));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(RIPE);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!(level instanceof ServerLevel server) || !(player instanceof ServerPlayer sp)) {
			return InteractionResult.SUCCESS;
		}
		if (!state.getValue(RIPE)) {
			sp.sendOverlayMessage(Component.translatable("eden.celestial.fruit.unripe"));
			return InteractionResult.CONSUME;
		}
		if (life && Exile.isExiled(sp)) {
			sp.sendOverlayMessage(Component.translatable("eden.celestial.fruit.exiled"));
			return InteractionResult.CONSUME;
		}
		server.setBlock(pos, state.setValue(RIPE, false), Block.UPDATE_ALL);
		server.scheduleTick(pos, this, REGROW_TICKS);
		server.sendParticles(life ? ParticleTypes.END_ROD : ParticleTypes.CRIMSON_SPORE, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 25, 0.3, 0.4, 0.3, 0.04);
		if (life) {
			sp.setHealth(sp.getMaxHealth());
			sp.getFoodData().setFoodLevel(20);
			sp.getFoodData().setSaturation(20.0F);
			CelestialData.update(sp, d -> d.withGrace(d.grace() + 2));
			server.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.2F, 1.0F);
			sp.sendOverlayMessage(Component.translatable("eden.celestial.fruit.life"));
			Lore.unlock(sp, "tree_life");
			Lore.unlock(sp, "eden");
		} else {
			sp.giveExperiencePoints(1000);
			CelestialData.update(sp, d -> d.withGrace(d.grace() + 1));
			server.playSound(null, pos, SoundEvents.GENERIC_EAT.value(), SoundSource.BLOCKS, 1.0F, 0.7F);
			if (consumeLeaf(sp)) {
				sp.sendOverlayMessage(Component.translatable("eden.celestial.fruit.leaf"));
			} else {
				sp.addEffect(new MobEffectInstance(ModEffects.EXILE, Exile.DURATION, 0, false, true, true));
				sp.sendOverlayMessage(Component.translatable("eden.celestial.fruit.knowledge"));
			}
			Lore.unlock(sp, "fruit");
		}
		return InteractionResult.SUCCESS;
	}

	private static boolean consumeLeaf(ServerPlayer player) {
		for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
			ItemStack stack = player.getInventory().getItem(i);
			if (stack.is(ModItems.FIG_LEAF)) {
				stack.shrink(1);
				return true;
			}
		}
		return false;
	}

	@Override
	protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		if (!state.getValue(RIPE)) {
			level.setBlock(pos, state.setValue(RIPE, true), Block.UPDATE_ALL);
		}
	}
}
