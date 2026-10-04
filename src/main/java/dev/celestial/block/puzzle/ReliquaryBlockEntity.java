package dev.celestial.block.puzzle;

import dev.celestial.registry.ModBlockEntities;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.UUIDUtil;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.phys.Vec3;

/** Таблица добычи и список тех, кто уже забрал награду (каждому — по одной, поэтому гонки между игроками нет). */
public class ReliquaryBlockEntity extends BlockEntity {
	private String lootTable = "";
	private final List<UUID> claimed = new ArrayList<>();

	public ReliquaryBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.RELIQUARY, pos, state);
	}

	public void claim(ServerLevel level, Player player) {
		if (claimed.contains(player.getUUID())) {
			player.sendOverlayMessage(Component.translatable("puzzle.celestial.reliquary.empty"));
			return;
		}
		if (lootTable.isEmpty()) {
			return;
		}
		claimed.add(player.getUUID());
		setChanged();
		LootTable table = level.getServer().reloadableRegistries().getLootTable(ResourceKey.create(Registries.LOOT_TABLE, Identifier.parse(lootTable)));
		LootParams params = new LootParams.Builder(level).withParameter(LootContextParams.ORIGIN, Vec3.atCenterOf(worldPosition))
			.withLuck(player.getLuck()).withParameter(LootContextParams.THIS_ENTITY, player).create(LootContextParamSets.CHEST);
		for (ItemStack stack : table.getRandomItems(params)) {
			if (!player.getInventory().add(stack)) {
				player.spawnAtLocation(level, stack);
			}
		}
		level.playSound(null, worldPosition, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.BLOCKS, 1.0F, 1.3F);
		level.sendParticles(ParticleTypes.END_ROD, worldPosition.getX() + 0.5, worldPosition.getY() + 1.1, worldPosition.getZ() + 0.5, 20, 0.3, 0.3, 0.3, 0.05);
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putString("LootTable", lootTable);
		output.store("Claimed", UUIDUtil.CODEC.listOf(), claimed);
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		lootTable = input.getStringOr("LootTable", "");
		claimed.clear();
		claimed.addAll(input.read("Claimed", UUIDUtil.CODEC.listOf()).orElse(List.of()));
	}
}
