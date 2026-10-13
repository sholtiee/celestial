package dev.celestial.astral;

import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.TagKey;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.LodestoneTracker;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.structure.Structure;

/**
 * Астролябия: ПКМ — найти ближайшее святилище хора (в Астрале) или Звёздный алтарь (крадучись) и навести на него стрелку,
 * как компас на магнетит. Вне Астрала звёзды молчат. Откат 3 с.
 */
public class AstrolabeItem extends Item {
	public static final TagKey<Structure> SHRINES = TagKey.create(Registries.STRUCTURE, dev.celestial.Celestial.id("star_shrines"));
	public static final TagKey<Structure> ALTARS = TagKey.create(Registries.STRUCTURE, dev.celestial.Celestial.id("star_altars"));

	public AstrolabeItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		if (!(level instanceof ServerLevel server)) {
			return InteractionResult.SUCCESS;
		}
		if (!level.dimension().equals(dev.celestial.world.dim.AbyssFeatures.ASTRAL)) {
			player.sendOverlayMessage(Component.translatable("item.celestial.astrolabe.silent"));
			return InteractionResult.FAIL;
		}
		boolean altar = player.isSecondaryUseActive();
		BlockPos found = server.findNearestMapStructure(altar ? ALTARS : SHRINES, player.blockPosition(), 64, false);
		player.getCooldowns().addCooldown(stack, 60);
		if (found == null) {
			player.sendOverlayMessage(Component.translatable("item.celestial.astrolabe.none"));
			return InteractionResult.FAIL;
		}
		stack.set(DataComponents.LODESTONE_TRACKER, new LodestoneTracker(Optional.of(GlobalPos.of(level.dimension(), found)), false));
		level.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.0F, 1.4F);
		player.sendOverlayMessage(Component.translatable(altar ? "item.celestial.astrolabe.altar" : "item.celestial.astrolabe.shrine",
			(int) Math.sqrt(found.distSqr(player.blockPosition()))));
		return InteractionResult.SUCCESS;
	}
}
