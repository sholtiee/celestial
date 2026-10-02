package dev.celestial.fading;

import dev.celestial.registry.ModBlocks;
import dev.celestial.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.projectile.throwableitemprojectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/** Метеорит: огненный камень с неба. При падении выбивает кратер со звёздным кварцем и метеоритным ядром. */
public class Meteor extends ThrowableItemProjectile {
	/** Скорость падения постоянна (вода и воздух её не гасят); после перезагрузки мира метеор просто исчезает. */
	private @org.jspecify.annotations.Nullable Vec3 speed;

	public Meteor(EntityType<? extends Meteor> type, Level level) {
		super(type, level);
	}

	public static Meteor launch(ServerLevel level, Vec3 from, Vec3 to) {
		Meteor meteor = new Meteor(ModEntities.METEOR, level);
		meteor.setPos(from);
		meteor.setItem(new ItemStack(ModBlocks.METEORITE));
		meteor.speed = to.subtract(from).normalize().scale(1.6);
		meteor.setDeltaMovement(meteor.speed);
		level.addFreshEntity(meteor);
		return meteor;
	}

	@Override
	protected Item getDefaultItem() {
		return ModBlocks.METEORITE.asItem();
	}

	@Override
	protected double getDefaultGravity() {
		return 0.0;
	}

	@Override
	public boolean isOnFire() {
		return true;
	}

	@Override
	public void tick() {
		if (!level().isClientSide()) {
			if (speed == null) {
				discard();
				return;
			}
			setDeltaMovement(speed);
		}
		super.tick();
		if (level().isClientSide()) {
			for (int i = 0; i < 4; i++) {
				level().addParticle(ParticleTypes.FLAME, getRandomX(0.8), getRandomY(), getRandomZ(0.8), 0, 0, 0);
				level().addParticle(ParticleTypes.LARGE_SMOKE, getRandomX(0.8), getRandomY(), getRandomZ(0.8), 0, 0.02, 0);
			}
			level().addParticle(ParticleTypes.END_ROD, getX(), getY(), getZ(), 0, 0, 0);
		} else if (tickCount > 600 || getY() < level().getMinY()) {
			discard();
		}
	}

	@Override
	protected void onHit(HitResult hit) {
		super.onHit(hit);
		if (level() instanceof ServerLevel level && !isRemoved()) {
			impact(level, BlockPos.containing(hit.getLocation()));
			discard();
		}
	}

	/** Кратер: воронка радиусом 3–4, по стенкам опалённый камень и звёздный кварц, в центре ядро. */
	public static void impact(ServerLevel level, BlockPos center) {
		RandomSource random = level.getRandom();
		level.explode(null, center.getX() + 0.5, center.getY() + 0.5, center.getZ() + 0.5, 3.0F, Level.ExplosionInteraction.NONE);
		int radius = 4 + random.nextInt(2);
		for (BlockPos pos : BlockPos.betweenClosed(center.offset(-radius - 1, -radius, -radius - 1), center.offset(radius + 1, radius, radius + 1))) {
			double dx = pos.getX() - center.getX();
			double dy = pos.getY() - center.getY();
			double dz = pos.getZ() - center.getZ();
			double d = Math.sqrt(dx * dx + dy * dy * 1.6 + dz * dz);
			BlockState state = level.getBlockState(pos);
			if (state.isAir() || state.getDestroySpeed(level, pos) < 0 || state.hasBlockEntity() || state.is(BlockTags.WITHER_IMMUNE)) {
				continue;
			}
			if (d < radius - 0.5 && dy >= -1) {
				level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
			} else if (d < radius + 0.7 && state.isSolid()) {
				float roll = random.nextFloat();
				BlockState wall = roll < 0.12F ? ModBlocks.STARQUARTZ_ORE.defaultBlockState()
					: roll < 0.25F ? Blocks.MAGMA_BLOCK.defaultBlockState()
					: roll < 0.6F ? Blocks.BLACKSTONE.defaultBlockState() : Blocks.BASALT.defaultBlockState();
				level.setBlock(pos, wall, 3);
			}
		}
		BlockPos core = center.below(radius - 2);
		while (level.getBlockState(core).isAir() && core.getY() > level.getMinY()) {
			core = core.below();
		}
		core = core.above();
		level.setBlock(core, ModBlocks.METEORITE.defaultBlockState(), 3);
		for (int i = 0; i < 6; i++) {
			BlockPos fire = core.offset(random.nextInt(5) - 2, 0, random.nextInt(5) - 2);
			if (level.getBlockState(fire).isAir() && level.getBlockState(fire.below()).isSolid()) {
				level.setBlock(fire, Blocks.FIRE.defaultBlockState(), 3);
			}
		}
		level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, center.getX() + 0.5, center.getY() + 1, center.getZ() + 0.5, 2, 1, 1, 1, 0);
		level.sendParticles(ParticleTypes.END_ROD, center.getX() + 0.5, center.getY() + 1, center.getZ() + 0.5, 120, 2, 2, 2, 0.3);
		level.playSound(null, center, dev.celestial.registry.ModSounds.METEOR_IMPACT, SoundSource.BLOCKS, 8.0F, 1.0F);
		final BlockPos corePos = core;
		level.getPlayers(p -> p.blockPosition().closerThan(corePos, 160)).forEach(p -> {
			p.sendSystemMessage(Component.translatable("fading.celestial.meteor_landed", corePos.getX(), corePos.getY(), corePos.getZ()));
			dev.celestial.data.CelestialData.update(p, d -> d.withCodex("place:meteor_crater"));
		});
	}
}
