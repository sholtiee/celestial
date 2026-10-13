package dev.celestial.astral;

import dev.celestial.data.CelestialData;
import dev.celestial.puzzle.Attempts;
import dev.celestial.puzzle.PuzzleRewards;
import dev.celestial.registry.ModBlockEntities;
import dev.celestial.registry.ModItems;
import java.util.HashSet;
import java.util.Set;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jspecify.annotations.Nullable;

/** Хор диска и сверка вставленных камней с рисунком созвездия. Пока не собран — охраняет поле от чужих блоков. */
public class StarDiskBlockEntity extends BlockEntity implements dev.celestial.puzzle.PuzzleZone {
	private String choirId = "";

	public StarDiskBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.STAR_DISK, pos, state);
	}

	public @Nullable Choir choir() {
		return Choir.byId(choirId);
	}

	public void setChoir(Choir c) {
		this.choirId = c.id;
		setChanged();
	}

	public boolean solved() {
		return getBlockState().getValue(StarDiskBlock.LIT);
	}

	/** Диск, к полю которого относится гнездо (в квадрате 5×5 на той же высоте). */
	public static @Nullable StarDiskBlockEntity find(ServerLevel level, BlockPos socket) {
		for (int dx = -2; dx <= 2; dx++) {
			for (int dz = -2; dz <= 2; dz++) {
				if (level.getBlockEntity(socket.offset(dx, 0, dz)) instanceof StarDiskBlockEntity disk) {
					return disk;
				}
			}
		}
		return null;
	}

	/** Не заблокирован ли игрок после ошибки (сообщение — внутри). */
	boolean mayTouch(ServerLevel level, Player player) {
		int left = Attempts.lockedSeconds(level, worldPosition, player);
		if (left > 0) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.locked_wait", left));
			return false;
		}
		return true;
	}

	/** Сверка: камней столько же, сколько звёзд (без центра) — верно или неверно. */
	void check(ServerLevel level, Player player) {
		Choir choir = choir();
		if (choir == null || solved()) {
			return;
		}
		Set<Integer> filled = new HashSet<>();
		filled.add(Choir.key(0, 0));
		for (int dx = -2; dx <= 2; dx++) {
			for (int dz = -2; dz <= 2; dz++) {
				BlockState st = level.getBlockState(worldPosition.offset(dx, 0, dz));
				if (st.getBlock() instanceof StarSocketBlock && st.getValue(StarSocketBlock.FILLED)) {
					filled.add(Choir.key(dx, dz));
				}
			}
		}
		Set<Integer> want = choir.cells();
		if (filled.size() < want.size()) {
			return;
		}
		if (filled.equals(want)) {
			level.setBlock(worldPosition, getBlockState().setValue(StarDiskBlock.LIT, true), Block.UPDATE_ALL);
			Attempts.reset(level, worldPosition, player);
			PuzzleRewards.solved(level, worldPosition, player, "star_disk", 16);
			if (player instanceof ServerPlayer sp) {
				CelestialData.update(sp, d -> d.withCodex("choir:" + choir.id));
				dev.celestial.lore.Lore.unlock(sp, "nine_choirs");  // Книга Чинов: первый собранный хор
				if (choir == Choir.ARCHANGELS) {
					dev.celestial.lore.Lore.unlock(sp, "archangels");
				}
				if (Choirs.count(CelestialData.get(sp)) >= 7) {
					dev.celestial.lore.Lore.unlock(sp, "morning_star_promise");  // алтарь открыт — «дам ему звезду утреннюю»
				}
				if (Choirs.patron(CelestialData.get(sp)) == null) {
					Choirs.setPatron(sp, choir);
				}
				dev.celestial.boss.BossIntro.title(sp, Component.translatable("choir.celestial.remembers").withStyle(ChatFormatting.AQUA),
					Component.translatable("choir.celestial." + choir.id).withStyle(ChatFormatting.ITALIC), 60);
				sp.sendSystemMessage(Component.translatable("choir.celestial.collected", Component.translatable("choir.celestial." + choir.id),
					Choirs.count(CelestialData.get(sp))));
			}
			for (int i = 0; i < 40; i++) {
				level.sendParticles(dev.celestial.registry.ModParticles.STARLIGHT, worldPosition.getX() + 0.5, worldPosition.getY() + 1 + i * 0.5,
					worldPosition.getZ() + 0.5, 3, 0.2, 0.2, 0.2, 0.01);
			}
			return;
		}
		// неверно: камни выпрыгивают, блокировка
		for (int dx = -2; dx <= 2; dx++) {
			for (int dz = -2; dz <= 2; dz++) {
				BlockPos p = worldPosition.offset(dx, 0, dz);
				BlockState st = level.getBlockState(p);
				if (st.getBlock() instanceof StarSocketBlock && st.getValue(StarSocketBlock.FILLED)) {
					level.setBlock(p, st.setValue(StarSocketBlock.FILLED, false), Block.UPDATE_ALL);
					ItemEntity drop = new ItemEntity(level, p.getX() + 0.5, p.getY() + 0.6, p.getZ() + 0.5, new ItemStack(ModItems.STAR_STONE), 0, 0.25, 0);
					level.addFreshEntity(drop);
				}
			}
		}
		Attempts.fail(level, worldPosition, player, Component.translatable("block.celestial.star_disk.wrong"));
	}

	@Override
	public boolean guards(BlockPos pos) {
		return !solved() && Math.abs(pos.getX() - worldPosition.getX()) <= 3 && Math.abs(pos.getZ() - worldPosition.getZ()) <= 3
			&& pos.getY() >= worldPosition.getY() - 1 && pos.getY() <= worldPosition.getY() + 3;
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		choirId = input.getStringOr("Choir", "");
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putString("Choir", choirId);
	}
}
