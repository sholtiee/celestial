package dev.celestial.mech;

import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModItems;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** Стопка на прессе и ход штампа. Изделия: пластины из слитков, гравий из булыжника, песок из гравия. */
public class DrivePressBlockEntity extends BlockEntity {
	public static final int STROKE = 30;
	private ItemStack input = ItemStack.EMPTY;
	private int progress;

	public DrivePressBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.DRIVE_PRESS, pos, state);
	}

	private static Map<Item, Item> recipes() {
		return Map.of(Items.IRON_INGOT, ModItems.IRON_PLATE, Items.COPPER_INGOT, ModItems.COPPER_PLATE,
			Items.GOLD_INGOT, ModItems.GOLD_PLATE, Items.COBBLESTONE, Items.GRAVEL, Items.GRAVEL, Items.SAND);
	}

	public static ItemStack result(ItemStack in) {
		Item out = recipes().get(in.getItem());
		return out == null ? ItemStack.EMPTY : new ItemStack(out);
	}

	boolean insert(ItemStack stack) {
		if (!input.isEmpty() && !ItemStack.isSameItemSameComponents(input, stack)) {
			return false;
		}
		int move = Math.min(stack.getCount(), stack.getMaxStackSize() - input.getCount());
		if (move <= 0) {
			return false;
		}
		if (input.isEmpty()) {
			input = stack.copyWithCount(move);
		} else {
			input.grow(move);
		}
		stack.shrink(move);
		setChanged();
		return true;
	}

	ItemStack take() {
		ItemStack out = input;
		input = ItemStack.EMPTY;
		progress = 0;
		setChanged();
		return out;
	}

	public static void serverTick(Level level, BlockPos pos, BlockState state, DrivePressBlockEntity be) {
		boolean working = !be.input.isEmpty() && Gears.driven(level, pos);
		if (working != state.getValue(DrivePressBlock.WORKING)) {
			level.setBlock(pos, state.setValue(DrivePressBlock.WORKING, working), Block.UPDATE_ALL);
		}
		if (!working) {
			be.progress = 0;
			return;
		}
		if (++be.progress < STROKE) {
			return;
		}
		be.progress = 0;
		ItemStack out = result(be.input);
		be.input.shrink(1);
		be.setChanged();
		ItemEntity drop = new ItemEntity(level, pos.getX() + 0.5, pos.getY() + 1.05, pos.getZ() + 0.5, out, 0, 0.12, 0);
		level.addFreshEntity(drop);
		level.playSound(null, pos, SoundEvents.ANVIL_LAND, SoundSource.BLOCKS, 0.35F, 1.4F);
		if (level instanceof ServerLevel server) {
			server.sendParticles(ParticleTypes.CRIT, pos.getX() + 0.5, pos.getY() + 1.0, pos.getZ() + 0.5, 6, 0.25, 0.05, 0.25, 0.1);
		}
	}

	@Override
	public void preRemoveSideEffects(BlockPos pos, BlockState state) {
		if (level != null && !input.isEmpty()) {
			level.addFreshEntity(new ItemEntity(level, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, input));
			input = ItemStack.EMPTY;
		}
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		this.input = input.read("Input", ItemStack.OPTIONAL_CODEC).orElse(ItemStack.EMPTY);
		progress = input.getIntOr("Progress", 0);
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		if (!input.isEmpty()) {
			output.store("Input", ItemStack.OPTIONAL_CODEC, input);
		}
		output.putInt("Progress", progress);
	}
}
