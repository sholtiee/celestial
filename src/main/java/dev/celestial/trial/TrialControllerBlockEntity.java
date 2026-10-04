package dev.celestial.trial;

import dev.celestial.Celestial;
import dev.celestial.data.CelestialData;
import dev.celestial.registry.ModBlockEntities;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.UUIDUtil;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.BossEvent;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/** Состояние испытания: кто проходит, какая волна, сколько осталось времени. */
public class TrialControllerBlockEntity extends BlockEntity {
	private static final int ARENA = 9;
	private String trialId = "heaven_1";
	private UUID challenger;
	private int wave = -1;
	private int ticksLeft;
	private final List<UUID> spawned = new ArrayList<>();
	private ServerBossEvent bar;
	/** После загрузки мира сущности волны ещё не загружены: пока ждём, не считаем их погибшими. */
	private int loadGrace;
	private net.minecraft.world.phys.Vec3 lastPos;

	public TrialControllerBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.TRIAL_CONTROLLER, pos, state);
	}

	public TrialDefinition definition() {
		return TrialDefinition.get(trialId);
	}

	public boolean isRunning() {
		return challenger != null;
	}

	public void start(ServerLevel level, Player player) {
		TrialDefinition def = definition();
		if (def == null || getBlockState().getValue(TrialControllerBlock.STATE) == TrialControllerBlock.TrialState.DONE) {
			player.sendOverlayMessage(Component.translatable("trial.celestial.done_already"));
			return;
		}
		if (isRunning()) {
			player.sendOverlayMessage(Component.translatable("trial.celestial.busy"));
			return;
		}
		if (def.type() == TrialDefinition.Type.BARE_WAVES && hasArmor(player)) {
			player.sendSystemMessage(Component.translatable("trial.celestial.remove_armor"));
			return;
		}
		challenger = player.getUUID();
		wave = -1;
		ticksLeft = def.timeLimitSeconds() * 20;
		level.setBlock(worldPosition, getBlockState().setValue(TrialControllerBlock.STATE, TrialControllerBlock.TrialState.RUNNING), Block.UPDATE_ALL);
		level.playSound(null, worldPosition, dev.celestial.registry.ModSounds.TRIAL_START, SoundSource.BLOCKS, 1.5F, 1.0F);
		player.sendSystemMessage(Component.translatable("trial.celestial.start." + def.type().name().toLowerCase()));
		createBar(player);
		if (def.type() == TrialDefinition.Type.PARKOUR) {
			TrialGuard.started(level, worldPosition);
		}
		lastPos = null;
		setChanged();
	}

	private void createBar(Player player) {
		bar = new ServerBossEvent(UUID.randomUUID(), Component.translatable("trial.celestial.name." + trialId), BossEvent.BossBarColor.YELLOW,
			BossEvent.BossBarOverlay.PROGRESS);
		if (player instanceof ServerPlayer sp) {
			bar.addPlayer(sp);
		}
	}

	private static boolean hasArmor(Player player) {
		for (EquipmentSlot slot : new EquipmentSlot[] {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET}) {
			if (!player.getItemBySlot(slot).isEmpty()) {
				return true;
			}
		}
		return false;
	}

	void serverTick(ServerLevel level) {
		if (!isRunning()) {
			return;
		}
		Player player = level.getPlayerByUUID(challenger);
		TrialDefinition def = definition();
		if (bar == null && player != null) {  // испытание продолжается после перезахода
			createBar(player);
		}
		if (loadGrace > 0) {
			loadGrace--;
			return;
		}
		if (player == null || !player.isAlive() || player.distanceToSqr(Vec3.atCenterOf(worldPosition)) > 48 * 48) {
			fail(level, "trial.celestial.fail.left");
			return;
		}
		if (def.type() == TrialDefinition.Type.BARE_WAVES && hasArmor(player)) {
			fail(level, "trial.celestial.fail.armor");
			return;
		}
		if (def.type() == TrialDefinition.Type.PARKOUR) {
			// жемчуг, элитры, верховая езда и левитация обходят пропасть: считаем это провалом
			var now = player.position();
			boolean cheat = player.isFallFlying() || player.isPassenger() || player.hasEffect(net.minecraft.world.effect.MobEffects.LEVITATION)
				|| player.hasEffect(net.minecraft.world.effect.MobEffects.SLOW_FALLING) || (lastPos != null && now.distanceToSqr(lastPos) > 64.0);
			lastPos = now;
			if (cheat) {
				fail(level, "trial.celestial.fail.cheat");
				return;
			}
			TrialGuard.started(level, worldPosition);  // идемпотентно; после перезахода защита от строительства включается заново
		}
		if (def.timeLimitSeconds() > 0) {
			ticksLeft--;
			bar.setProgress(Math.max(0, ticksLeft / (def.timeLimitSeconds() * 20.0F)));
			if (ticksLeft <= 0) {
				fail(level, "trial.celestial.fail.time");
				return;
			}
		}
		switch (def.type()) {
			case WAVES, BARE_WAVES -> tickWaves(level, def);
			case PUZZLE -> {
				if (level.getGameTime() % 10 == 0 && puzzleSolvedNearby(level)) {
					succeed(level, player);
				}
			}
			case PARKOUR -> { }
		}
	}

	private void tickWaves(ServerLevel level, TrialDefinition def) {
		spawned.removeIf(id -> {
			Entity e = level.getEntity(id);
			return e == null || !e.isAlive();
		});
		bar.setProgress(def.waves().isEmpty() ? 1 : Math.max(0, 1 - (wave + (spawned.isEmpty() ? 1 : 0.5F)) / def.waves().size()));
		if (!spawned.isEmpty() || level.getGameTime() % 20 != 0) {
			return;
		}
		wave++;
		if (wave >= def.waves().size()) {
			Player player = level.getPlayerByUUID(challenger);
			if (player != null) {
				succeed(level, player);
			}
			return;
		}
		for (TrialDefinition.Spawn s : def.waves().get(wave)) {
			for (int i = 0; i < s.count(); i++) {
				Entity e = s.type().get().create(level, EntitySpawnReason.TRIAL_SPAWNER);
				if (e == null) {
					continue;
				}
				e.addTag(dev.celestial.world.abyss.Darkness.NO_REPEL);  // Оберег рядом не должен стирать мобов волны (иначе волна «проходится» сама)
				double a = level.getRandom().nextDouble() * Math.PI * 2;
				double r = 3 + level.getRandom().nextDouble() * (ARENA - 4);
				BlockPos at = BlockPos.containing(worldPosition.getX() + 0.5 + Math.cos(a) * r, worldPosition.getY() + 1, worldPosition.getZ() + 0.5 + Math.sin(a) * r);
				e.snapTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, level.getRandom().nextFloat() * 360, 0);
				if (e instanceof Mob mob) {
					mob.finalizeSpawn(level, level.getCurrentDifficultyAt(at), EntitySpawnReason.TRIAL_SPAWNER, null);
					mob.setPersistenceRequired();
					mob.setTarget(level.getPlayerByUUID(challenger));
				}
				level.addFreshEntity(e);
				level.sendParticles(ParticleTypes.TRIAL_SPAWNER_DETECTED_PLAYER, e.getX(), e.getY() + 0.5, e.getZ(), 15, 0.3, 0.5, 0.3, 0.01);
				spawned.add(e.getUUID());
			}
		}
		level.playSound(null, worldPosition, SoundEvents.TRIAL_SPAWNER_SPAWN_MOB, SoundSource.BLOCKS, 1.0F, 1.0F);
	}

	/** Загадка на этаже решена, если любой блок загадки в арене выдаёт сигнал. */
	private boolean puzzleSolvedNearby(ServerLevel level) {
		AABB box = new AABB(worldPosition).inflate(ARENA, 4, ARENA);
		for (BlockPos p : BlockPos.betweenClosed(BlockPos.containing(box.minX, box.minY, box.minZ), BlockPos.containing(box.maxX, box.maxY, box.maxZ))) {
			BlockState s = level.getBlockState(p);
			String path = net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(s.getBlock()).getPath();
			boolean puzzle = path.equals("light_receiver") || path.equals("bell_altar") || path.equals("star_tile") || path.equals("rune_pedestal");
			// приёмники света считаются только родные (sealed): свой приёмник в арене испытание не проходит
			if (path.equals("light_receiver") && !s.getValue(dev.celestial.block.light.LightReceiverBlock.SEALED)) {
				continue;
			}
			if (puzzle && s.getSignal(level, p, net.minecraft.core.Direction.UP) > 0) {
				return true;
			}
		}
		return false;
	}

	/** Вызывается Финишным кристаллом в испытании на время. */
	public void reachGoal(ServerLevel level, Player player) {
		if (isRunning() && player.getUUID().equals(challenger) && definition().type() == TrialDefinition.Type.PARKOUR) {
			succeed(level, player);
		}
	}

	private void succeed(ServerLevel level, Player player) {
		TrialDefinition def = definition();
		level.setBlock(worldPosition, getBlockState().setValue(TrialControllerBlock.STATE, TrialControllerBlock.TrialState.DONE), Block.UPDATE_ALL);
		level.playSound(null, worldPosition, SoundEvents.TRIAL_SPAWNER_OPEN_SHUTTER, SoundSource.BLOCKS, 1.0F, 1.4F);
		level.playSound(null, worldPosition, SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.BLOCKS, 1.0F, 1.0F);
		level.sendParticles(ParticleTypes.END_ROD, worldPosition.getX() + 0.5, worldPosition.getY() + 1.5, worldPosition.getZ() + 0.5, 80, 1, 1, 1, 0.2);
		player.sendSystemMessage(Component.translatable("trial.celestial.success", Component.translatable("trial.celestial.name." + trialId), def.grace()));
		CelestialData.update(player, d -> d.withGrace(d.grace() + def.grace()).withTrial(trialId));
		dropReward(level, player);
		openSeals(level);
		cleanup();
	}

	/** Растворяет печать-двери этажа (проход наверх). */
	private void openSeals(ServerLevel level) {
		for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-ARENA - 1, -2, -ARENA - 1), worldPosition.offset(ARENA + 1, 8, ARENA + 1))) {
			if (level.getBlockState(p).is(dev.celestial.registry.ModBlocks.SEALED_DOOR)) {
				dev.celestial.block.puzzle.SealedDoorBlock.dissolve(level, p.immutable());
			}
		}
	}

	private void dropReward(ServerLevel level, Player player) {
		ResourceKey<LootTable> key = ResourceKey.create(Registries.LOOT_TABLE, Celestial.id("chests/trial_" + trialId));
		LootTable table = level.getServer().reloadableRegistries().getLootTable(key);
		LootParams params = new LootParams.Builder(level).withParameter(LootContextParams.ORIGIN, Vec3.atCenterOf(worldPosition))
			.withLuck(player.getLuck()).withParameter(LootContextParams.THIS_ENTITY, player).create(LootContextParamSets.CHEST);
		for (var stack : table.getRandomItems(params)) {
			Block.popResource(level, worldPosition.above(), stack);
		}
	}

	private void fail(ServerLevel level, String reason) {
		Player player = challenger == null ? null : level.getPlayerByUUID(challenger);
		if (player != null) {
			player.sendSystemMessage(Component.translatable(reason));
		}
		for (UUID id : spawned) {
			Entity e = level.getEntity(id);
			if (e != null) {
				e.discard();
			}
		}
		level.setBlock(worldPosition, getBlockState().setValue(TrialControllerBlock.STATE, TrialControllerBlock.TrialState.IDLE), Block.UPDATE_ALL);
		level.playSound(null, worldPosition, SoundEvents.TRIAL_SPAWNER_CLOSE_SHUTTER, SoundSource.BLOCKS, 1.0F, 0.8F);
		cleanup();
	}

	private void cleanup() {
		if (level instanceof ServerLevel server) {
			TrialGuard.ended(server, worldPosition);
		}
		challenger = null;
		spawned.clear();
		wave = -1;
		if (bar != null) {
			bar.removeAllPlayers();
			bar = null;
		}
		setChanged();
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putString("Trial", trialId);
		// состояние хода испытания: раньше терялось, блок оставался «идёт», а мобы волны — вечными
		if (challenger != null) {
			output.putString("Challenger", challenger.toString());
			output.putInt("Wave", wave);
			output.putInt("TicksLeft", ticksLeft);
			output.store("Spawned", net.minecraft.core.UUIDUtil.CODEC.listOf(), new ArrayList<>(spawned));
		}
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		trialId = input.getStringOr("Trial", "heaven_1");
		String who = input.getStringOr("Challenger", "");
		challenger = null;
		spawned.clear();
		if (!who.isEmpty()) {
			try {
				challenger = UUID.fromString(who);
				wave = input.getIntOr("Wave", -1);
				ticksLeft = input.getIntOr("TicksLeft", 0);
				spawned.addAll(input.read("Spawned", net.minecraft.core.UUIDUtil.CODEC.listOf()).orElse(List.of()));
				loadGrace = 100;
			} catch (IllegalArgumentException e) {
				challenger = null;
			}
		}
	}
}
