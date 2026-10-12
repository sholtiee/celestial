package dev.celestial.block.puzzle.time;

import dev.celestial.puzzle.PuzzleRewards;
import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModBlocks;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;

/**
 * «Комната-перемотка». При первой загрузке ядро запоминает каждый блок своей комнаты ({@code From}..{@code To} от себя).
 * Раз в {@link #CYCLE} тиков всё, что изменили, возвращается — построенное исчезает, сломанное встаёт, зажжённые якоря гаснут.
 * Решение — зажечь все якоря за один оборот (строить можно — но на один оборот). Снимок хранится в NBT, перезаход его не сбивает.
 */
public class RewindCoreBlockEntity extends BlockEntity {
	public static final int CYCLE = 900;
	private int[] from = {-8, -1, -8};
	private int[] to = {8, 10, 8};
	private final List<BlockState> palette = new ArrayList<>();
	private int[] data = new int[0];
	private boolean solved;
	private int clock;

	public RewindCoreBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.REWIND_CORE, pos, state);
	}

	private BlockPos min() {
		return worldPosition.offset(from[0], from[1], from[2]);
	}

	private BlockPos max() {
		return worldPosition.offset(to[0], to[1], to[2]);
	}

	public AABB room() {
		return AABB.encapsulatingFullBlocks(min(), max());
	}

	private void capture(ServerLevel level) {
		palette.clear();
		Map<BlockState, Integer> index = new HashMap<>();
		List<Integer> out = new ArrayList<>();
		for (BlockPos p : BlockPos.betweenClosed(min(), max())) {
			BlockState s = level.getBlockState(p);
			out.add(index.computeIfAbsent(s, k -> {
				palette.add(k);
				return palette.size() - 1;
			}));
		}
		data = out.stream().mapToInt(Integer::intValue).toArray();
		setChanged();
		restock(level);
	}

	/** Бочка с припасами в комнате каждый оборот снова полна: строить можно — но лишь на один оборот. */
	private void restock(ServerLevel level) {
		for (BlockPos p : BlockPos.betweenClosed(min(), max())) {
			if (level.getBlockEntity(p) instanceof net.minecraft.world.level.block.entity.BarrelBlockEntity barrel) {
				barrel.clearContent();
				barrel.setItem(0, new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.COBBLED_DEEPSLATE, 48));
				barrel.setItem(1, new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.LADDER, 16));
				barrel.setItem(2, new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.IRON_PICKAXE));
			}
		}
	}

	/** Вернуть комнату к снимку; построенное игроком исчезает без выпадения, выпавшие в комнате вещи — тоже. */
	private void rewind(ServerLevel level) {
		int i = 0;
		int changed = 0;
		for (BlockPos p : BlockPos.betweenClosed(min(), max())) {
			if (i >= data.length) {
				break;
			}
			BlockState want = palette.get(data[i++]);
			if (!level.getBlockState(p).equals(want)) {
				level.setBlock(p, want, Block.UPDATE_ALL | Block.UPDATE_SUPPRESS_DROPS);
				changed++;
				if (changed % 3 == 0) {
					level.sendParticles(ParticleTypes.REVERSE_PORTAL, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 3, 0.3, 0.3, 0.3, 0.02);
				}
			}
		}
		for (ItemEntity item : level.getEntitiesOfClass(ItemEntity.class, room())) {
			item.discard();
		}
		restock(level);
		level.playSound(null, worldPosition, SoundEvents.BEACON_DEACTIVATE, SoundSource.BLOCKS, 2.0F, 0.6F);
		level.playSound(null, worldPosition, SoundEvents.BELL_BLOCK, SoundSource.BLOCKS, 2.0F, 0.5F);
		for (ServerPlayer player : level.getEntitiesOfClass(ServerPlayer.class, room().inflate(4))) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.rewind_room.rewound"));
		}
	}

	void tick(ServerLevel level) {
		if (data.length == 0) {
			if (level.hasChunksAt(min(), max())) {  // снимок — только когда вся комната загружена (шаблон мог встать в несколько чанков)
				capture(level);
			}
			return;
		}
		if (solved) {
			return;
		}
		clock++;
		int left = CYCLE - clock;
		if (left == 200 || left == 100 || left <= 60 && left % 20 == 0 && left > 0) {
			level.playSound(null, worldPosition, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.BLOCKS, 1.5F, left <= 60 ? 1.6F : 1.0F);
		}
		if (clock % 20 == 0) {
			for (ServerPlayer player : level.getEntitiesOfClass(ServerPlayer.class, room().inflate(2))) {
				player.sendOverlayMessage(Component.translatable("puzzle.celestial.rewind_room.left", left / 20));
			}
		}
		if (clock >= CYCLE) {
			clock = 0;
			rewind(level);
		}
	}

	/** Якорь зажгли: все ли горят? */
	void anchorLit(ServerLevel level, Player player) {
		if (solved) {
			return;
		}
		List<BlockPos> anchors = new ArrayList<>();
		for (BlockPos p : BlockPos.betweenClosed(min(), max())) {
			if (level.getBlockState(p).is(ModBlocks.REWIND_ANCHOR)) {
				anchors.add(p.immutable());
			}
		}
		long lit = anchors.stream().filter(p -> level.getBlockState(p).getValue(RewindAnchorBlock.LIT)).count();
		player.sendOverlayMessage(Component.translatable("puzzle.celestial.rewind_room.anchors", lit, anchors.size()));
		if (!anchors.isEmpty() && lit == anchors.size() && !player.isCreative()) {
			solved = true;
			setChanged();
			PuzzleRewards.solved(level, BlockPos.containing(room().getCenter()), player, "rewind_room", 14);  // ядро под потолком: печати ищем от середины комнаты
		}
	}

	public boolean solved() {
		return solved;
	}

	static RewindCoreBlockEntity find(ServerLevel level, BlockPos near) {
		for (BlockPos p : BlockPos.betweenClosed(near.offset(-16, -12, -16), near.offset(16, 12, 16))) {
			if (level.getBlockEntity(p) instanceof RewindCoreBlockEntity c && c.room().inflate(1).contains(net.minecraft.world.phys.Vec3.atCenterOf(near))) {
				return c;
			}
		}
		return null;
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putIntArray("From", from);
		output.putIntArray("To", to);
		output.putBoolean("Solved", solved);
		output.putInt("Clock", clock);
		if (data.length > 0) {
			output.store("Palette", BlockState.CODEC.listOf(), palette);
			output.putIntArray("Data", data);
		}
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		input.getIntArray("From").filter(a -> a.length == 3).ifPresent(a -> from = a);
		input.getIntArray("To").filter(a -> a.length == 3).ifPresent(a -> to = a);
		solved = input.getBooleanOr("Solved", false);
		clock = input.getIntOr("Clock", 0);
		palette.clear();
		input.read("Palette", BlockState.CODEC.listOf()).ifPresent(palette::addAll);
		data = input.getIntArray("Data").orElse(new int[0]);
		if (palette.isEmpty()) {
			data = new int[0];
		}
	}
}
