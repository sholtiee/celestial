package dev.celestial.astral;

import dev.celestial.data.CelestialData;
import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.item.context.UseOnContext;
import org.jspecify.annotations.Nullable;

/**
 * Звёздный кристалл (качество кристаллов, PLAN 0.6): у каждого своя чистота 1–100 % (назначается при первом попадании в инвентарь,
 * высокая — редкость). ПКМ по зажжённому Звёздному диску собранного хора — настроить хор: благословение этого хора, когда он покровитель,
 * сильнее в (1 + чистота/100) раз. Настройку меняет только кристалл чище прежнего; запись Кодекса {@code attune:<хор>:<чистота>}.
 */
public class StarCrystalItem extends Item {
	public StarCrystalItem(Properties properties) {
		super(properties);
	}

	public static int purity(ItemStack stack) {
		CustomData data = stack.get(DataComponents.CUSTOM_DATA);
		return data == null ? 0 : data.copyTag().getIntOr("Purity", 0);
	}

	public static void setPurity(ItemStack stack, int purity) {
		CompoundTag tag = new CompoundTag();
		tag.putInt("Purity", purity);
		stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
	}

	@Override
	public void inventoryTick(ItemStack stack, ServerLevel level, Entity owner, @Nullable EquipmentSlot slot) {
		if (purity(stack) == 0) {
			double r = level.getRandom().nextDouble();
			setPurity(stack, 1 + (int) (99 * r * r));  // чистые кристаллы редки
		}
	}

	@Override
	@SuppressWarnings("deprecation")
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> builder, TooltipFlag flag) {
		int p = purity(stack);
		builder.accept(p == 0 ? Component.translatable("item.celestial.star_crystal.unknown").withStyle(ChatFormatting.GRAY)
			: Component.translatable("item.celestial.star_crystal.purity", p).withStyle(p >= 80 ? ChatFormatting.LIGHT_PURPLE : p >= 50 ? ChatFormatting.AQUA : ChatFormatting.GRAY));
		builder.accept(Component.translatable("item.celestial.star_crystal.hint").withStyle(ChatFormatting.DARK_GRAY));
	}

	@Override
	public InteractionResult useOn(UseOnContext ctx) {
		if (!(ctx.getPlayer() instanceof ServerPlayer sp) || !(ctx.getLevel().getBlockEntity(ctx.getClickedPos()) instanceof StarDiskBlockEntity disk)) {
			return InteractionResult.PASS;
		}
		Choir choir = disk.choir();
		ItemStack stack = ctx.getItemInHand();
		int p = purity(stack);
		if (choir == null || p == 0 || !ctx.getLevel().getBlockState(ctx.getClickedPos()).getValue(StarDiskBlock.LIT)
				|| !Choirs.collected(CelestialData.get(sp), choir)) {
			sp.sendOverlayMessage(Component.translatable("choir.celestial.attune.not_ready"));
			return InteractionResult.FAIL;
		}
		int current = Choirs.attunement(CelestialData.get(sp), choir);
		if (p <= current) {
			sp.sendOverlayMessage(Component.translatable("choir.celestial.attune.dimmer", current));
			return InteractionResult.FAIL;
		}
		CelestialData.update(sp, d -> {
			var out = d;
			for (String e : d.codex()) {
				if (e.startsWith("attune:" + choir.id + ":")) {
					out = out.withoutCodex(e);
				}
			}
			return out.withCodex("attune:" + choir.id + ":" + p);
		});
		if (!sp.isCreative()) {
			stack.shrink(1);
		}
		Choirs.apply(sp);
		sp.sendSystemMessage(Component.translatable("choir.celestial.attune.done", Component.translatable("choir.celestial." + choir.id), p)
			.withStyle(ChatFormatting.AQUA));
		ctx.getLevel().playSound(null, ctx.getClickedPos(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 1.0F, 1.2F);
		return InteractionResult.SUCCESS;
	}
}
