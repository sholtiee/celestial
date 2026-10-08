package dev.celestial.block;

import dev.celestial.data.CelestialData;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Неопалимая купина (Исх. 3:2–5): куст, который горит и не сгорает. Неразрушим, греет как костёр (см. Cold.nearHeat). «Сними обувь твою»: ПКМ в обуви отбрасывает,
 * босой игрок получает полное тепло.
 */
public class BurningBushBlock extends Block {
	private static final VoxelShape SHAPE = Block.box(2, 0, 2, 14, 14, 14);

	public BurningBushBlock(Properties properties) {
		super(properties);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (player instanceof ServerPlayer sp) {
			if (!sp.getItemBySlot(EquipmentSlot.FEET).isEmpty()) {
				Vec3 away = sp.position().subtract(Vec3.atCenterOf(pos)).multiply(1, 0, 1).normalize().scale(0.8);
				sp.push(away.x, 0.3, away.z);
				sp.syncVelocity = true;  // игроку скорость уходит только по этому флагу (его же ставит урон)
				sp.sendOverlayMessage(Component.translatable("block.celestial.burning_bush.shoes"));
			} else {
				CelestialData.update(sp, d -> d.withWarmth(100.0F));
				sp.sendOverlayMessage(Component.translatable("block.celestial.burning_bush.warm"));
			}
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		if (random.nextInt(3) == 0) {
			level.addParticle(ParticleTypes.FLAME, pos.getX() + 0.2 + random.nextDouble() * 0.6, pos.getY() + 0.6 + random.nextDouble() * 0.7, pos.getZ() + 0.2 + random.nextDouble() * 0.6, 0, 0.02, 0);
		}
		if (random.nextInt(8) == 0) {
			level.addParticle(ParticleTypes.LAVA, pos.getX() + 0.5, pos.getY() + 1.0, pos.getZ() + 0.5, 0, 0, 0);
		}
	}
}
