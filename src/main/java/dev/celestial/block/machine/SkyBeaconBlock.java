package dev.celestial.block.machine;

import dev.celestial.data.BeaconNetwork;
import dev.celestial.data.CelestialData;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import org.jspecify.annotations.Nullable;

/**
 * Небесный маяк: точка сети телепортов (между любыми измерениями). Имя берётся из названия предмета (переименуй на наковальне).
 * ПКМ — список маяков в чате, клик по строке — перенос.
 */
public class SkyBeaconBlock extends Block {
	public SkyBeaconBlock(Properties properties) {
		super(properties);
	}

	@Override
	public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity by, ItemStack stack) {
		if (level instanceof ServerLevel server) {
			String name = stack.has(net.minecraft.core.component.DataComponents.CUSTOM_NAME) ? stack.getHoverName().getString()
				: "Маяк " + pos.getX() + " " + pos.getZ();
			CelestialData.updateBeacons(server.getServer(), n -> n.with(new BeaconNetwork.Beacon(level.dimension().identifier().toString(), pos, name)));
		}
	}

	@Override
	public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
		if (level instanceof ServerLevel server) {
			CelestialData.updateBeacons(server.getServer(), n -> n.without(level.dimension().identifier().toString(), pos));
		}
		return super.playerWillDestroy(level, pos, state, player);
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (level instanceof ServerLevel server) {
			String dim = level.dimension().identifier().toString();
			if (CelestialData.beacons(server.getServer()).beacons().stream().noneMatch(b -> b.pos().equals(pos) && b.dimension().equals(dim))) {
				// маяк из сгенерированной постройки зажигается при первом касании
				CelestialData.updateBeacons(server.getServer(), n -> n.with(new BeaconNetwork.Beacon(dim, pos, "Маяк " + pos.getX() + " " + pos.getZ())));
			}
			List<BeaconNetwork.Beacon> all = CelestialData.beacons(server.getServer()).beacons();
			player.sendSystemMessage(Component.translatable("machine.celestial.beacon.header").withStyle(ChatFormatting.GOLD));
			for (int i = 0; i < all.size(); i++) {
				BeaconNetwork.Beacon b = all.get(i);
				boolean here = b.pos().equals(pos) && b.dimension().equals(level.dimension().identifier().toString());
				MutableComponent line = Component.literal((here ? " ● " : " ✦ ") + b.name() + "  ")
					.withStyle(here ? ChatFormatting.GRAY : ChatFormatting.AQUA)
					.append(Component.literal("[" + b.dimension().replace("minecraft:", "").replace("celestial:", "") + " "
						+ b.pos().getX() + " " + b.pos().getY() + " " + b.pos().getZ() + "]").withStyle(ChatFormatting.DARK_GRAY));
				if (!here) {
					line = line.withStyle(style -> style.withClickEvent(new ClickEvent.RunCommand("/celestial beacon " + b.pos().getX() + " "
						+ b.pos().getY() + " " + b.pos().getZ() + " " + b.dimension()))
						.withHoverEvent(new HoverEvent.ShowText(Component.translatable("machine.celestial.beacon.click"))));
				}
				player.sendSystemMessage(line);
			}
		}
		return InteractionResult.SUCCESS;
	}
}
