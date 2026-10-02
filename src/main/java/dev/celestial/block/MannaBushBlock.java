package dev.celestial.block;

import dev.celestial.Celestial;
import dev.celestial.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.InsideBlockEffectApplier;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SweetBerryBushBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.phys.BlockHitResult;

/** Манна-куст: как ягодный куст, но не колется и даёт манну. */
public class MannaBushBlock extends SweetBerryBushBlock {
	public static final ResourceKey<LootTable> HARVEST = ResourceKey.create(Registries.LOOT_TABLE, Celestial.id("harvest/manna_bush"));

	public MannaBushBlock(Properties properties) {
		super(properties);
	}

	@Override
	protected ItemStack getCloneItemStack(LevelReader level, BlockPos pos, BlockState state, boolean includeData) {
		return new ItemStack(ModItems.MANNA_BERRIES);
	}

	@Override
	protected void entityInside(BlockState state, Level level, BlockPos pos, Entity entity, InsideBlockEffectApplier effectApplier, boolean isPrecise) {
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hitResult) {
		if (state.getValue(AGE) <= 1) {
			return InteractionResult.PASS;
		}
		if (level instanceof ServerLevel serverLevel) {
			Block.dropFromBlockInteractLootTable(serverLevel, HARVEST, pos, state, null, null, player,
				(lvl, stack) -> Block.popResource(lvl, pos, stack));
			serverLevel.playSound(null, pos, SoundEvents.SWEET_BERRY_BUSH_PICK_BERRIES, SoundSource.BLOCKS, 1.0F, 1.2F);
			BlockState newState = state.setValue(AGE, 1);
			serverLevel.setBlock(pos, newState, Block.UPDATE_CLIENTS);
			serverLevel.gameEvent(GameEvent.BLOCK_CHANGE, pos, GameEvent.Context.of(player, newState));
		}
		return InteractionResult.SUCCESS;
	}
}
