package dev.celestial.boss;

import dev.celestial.story.Story;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.UUIDUtil;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * Учёт боя с боссом для достижений «без единой царапины» и «быстрее …». Босс вызывает {@link #tick} каждый шаг ИИ,
 * {@link #dealt} из hurtServer и {@link #finish} в die. «Участник» — игрок, который был в полосе босса в первые
 * {@link #JOIN_WINDOW} тиков боя (кто пришёл позже, достижение за чистую победу не получает); «ранен» — у него
 * хоть раз упали здоровье + поглощение (от чего угодно: босс, слуги, голод, падение).
 */
public final class BossRecord {
	/** Сколько тиков после начала боя ещё можно «успеть» в участники. */
	private static final int JOIN_WINDOW = 200;

	private long start = -1;
	private final Set<UUID> participants = new HashSet<>();
	private final Set<UUID> hurt = new HashSet<>();
	private final Set<UUID> dealt = new HashSet<>();
	private final Map<UUID, Float> last = new HashMap<>();

	/** Каждый шаг ИИ босса: `players` — те, кто видит полосу босса. */
	public void tick(ServerLevel level, Collection<ServerPlayer> players) {
		if (start < 0) {
			start = level.getGameTime();
		}
		boolean joining = level.getGameTime() - start <= JOIN_WINDOW;
		for (ServerPlayer p : players) {
			if (p.isCreative() || p.isSpectator()) {
				continue;
			}
			UUID id = p.getUUID();
			if (joining) {
				participants.add(id);
			}
			float now = p.getHealth() + p.getAbsorptionAmount();
			Float before = last.put(id, now);
			if (before != null && now < before - 0.001F) {
				hurt.add(id);
			}
		}
	}

	/** Игрок реально ранил босса. */
	public void dealt(DamageSource source) {
		if (source.getEntity() instanceof ServerPlayer p) {
			dealt.add(p.getUUID());
		}
	}

	/** Босс пал: выдаёт «чистую победу» и «быструю победу» тем, кто бил босса и стоял рядом. */
	public void finish(ServerLevel level, Collection<ServerPlayer> players, Story flawless, Story swift, int swiftTicks) {
		if (start < 0) {
			return;
		}
		boolean fast = level.getGameTime() - start <= swiftTicks;
		for (ServerPlayer p : players) {
			UUID id = p.getUUID();
			if (!dealt.contains(id) || p.isCreative() || p.isSpectator()) {
				continue;
			}
			if (fast) {
				swift.grant(p);
			}
			if (participants.contains(id) && !hurt.contains(id)) {
				flawless.grant(p);
			}
		}
	}

	public void save(ValueOutput output) {
		output.putLong("FightStart", start);
		output.store("FightPlayers", UUIDUtil.CODEC.listOf(), List.copyOf(participants));
		output.store("FightHurt", UUIDUtil.CODEC.listOf(), List.copyOf(hurt));
		output.store("FightDealt", UUIDUtil.CODEC.listOf(), List.copyOf(dealt));
	}

	public void load(ValueInput input) {
		start = input.getLongOr("FightStart", -1L);
		participants.clear();
		hurt.clear();
		dealt.clear();
		input.read("FightPlayers", UUIDUtil.CODEC.listOf()).ifPresent(participants::addAll);
		input.read("FightHurt", UUIDUtil.CODEC.listOf()).ifPresent(hurt::addAll);
		input.read("FightDealt", UUIDUtil.CODEC.listOf()).ifPresent(dealt::addAll);
	}
}
