package dev.celestial.chrono;

import dev.celestial.Celestial;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentSyncPredicate;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Ход времени для сущностей (Акт IV). У каждой сущности — масштаб хода: 0 стоит, 0.5 замедлена, 1 обычно, 2 ускорена.
 * Масштаб &lt; 1 — сущность пропускает тики ({@link #skipTick}, вызывается из TickRateManager.isEntityFrozen на сервере и клиенте);
 * &gt; 1 — лишний тик на сервере ({@link #extraTicks}). Игрокам тики не трогаем (ломает ввод) — им модификаторы атрибутов.
 * Источники (маятники, Песочные часы, Часовщик) каждый тик заявляют свои зоны; в конце тика масштабы сводятся и
 * синхронизируются клиенту вложением {@link #SCALE}. Без заявки масштаб снимается — источник пропал, время пошло.
 */
public final class TimeFlow {
	public static final AttachmentType<Float> SCALE = AttachmentRegistry.<Float>builder()
		.syncWith(ByteBufCodecs.FLOAT, AttachmentSyncPredicate.all())
		.buildAndRegister(Celestial.id("time_scale"));

	/** Боссы и прочие, кого нельзя остановить: для них остановка — лишь замедление. */
	public static final TagKey<EntityType<?>> IMMUNE = TagKey.create(Registries.ENTITY_TYPE, Celestial.id("time_immune"));
	public static final float IMMUNE_MIN = 0.5F;

	public static final float STOP = 0.0F;
	public static final float SLOW = 0.5F;
	public static final float FAST = 2.0F;

	private static final Identifier MOD_SPEED = Celestial.id("time_speed");
	private static final Identifier MOD_JUMP = Celestial.id("time_jump");
	private static final Identifier MOD_GRAVITY = Celestial.id("time_gravity");
	private static final Identifier MOD_ATTACK = Celestial.id("time_attack");

	/** Заявки этого тика: сущность → произведение масштабов (остановка побеждает). */
	private static final Map<ResourceKey<Level>, Map<Entity, Float>> CLAIMS = new HashMap<>();
	/** Сущности, у которых масштаб сейчас не 1 (чтобы снять его, когда заявок нет). */
	private static final Map<ResourceKey<Level>, Set<Entity>> ACTIVE = new HashMap<>();
	/** Пузыри остановки (Песочные часы, «Стой!» Часовщика). */
	private static final List<Bubble> BUBBLES = new ArrayList<>();

	/** Пузырь остановленного времени. {@code exempt} — кто не замирает (владелец часов, его снаряды; босс). */
	public record Bubble(ResourceKey<Level> level, Vec3 center, double radius, long until, float scale, boolean players, @Nullable UUID exempt) {}

	private TimeFlow() {}

	public static void init() {
		ServerTickEvents.END_LEVEL_TICK.register(TimeFlow::commit);
	}

	// ── чтение ──

	public static float scale(Entity entity) {
		Float s = entity.getAttached(SCALE);
		return s == null ? 1.0F : s;
	}

	/** Пропустить ли тик (масштаб &lt; 1). Детерминированно: тик проходит, когда целая часть {@code t·s} растёт. */
	public static boolean skipTick(Entity entity) {
		if (entity instanceof Player) {
			return false;
		}
		Float s = entity.getAttached(SCALE);
		if (s == null || s >= 1.0F) {
			return false;
		}
		if (s <= 0.0F) {
			return true;
		}
		if (entity.level().isClientSide()) {
			// на клиенте замедлённую сущность не дёргаем пропусками (кадры прыгали бы), её плавно ведут позиции с сервера
			return false;
		}
		long t = entity.level().getGameTime() + (entity.getId() & 7);
		return Math.floor((t + 1) * s) <= Math.floor(t * s);
	}

	/** Сколько лишних тиков дать сущности в этот тик (масштаб &gt; 1). */
	public static int extraTicks(Entity entity) {
		if (entity instanceof Player) {
			return 0;
		}
		Float s = entity.getAttached(SCALE);
		if (s == null || s <= 1.0F) {
			return 0;
		}
		long t = entity.level().getGameTime() + (entity.getId() & 7);
		return (int) (Math.floor((t + 1) * s) - Math.floor(t * s)) - 1;
	}

	// ── заявки ──

	/** Заявить масштаб для сущности на этот тик (вызывают источники во время тика). */
	public static void claim(Entity entity, float scale) {
		if (!(entity.level() instanceof ServerLevel level) || entity.isRemoved()) {
			return;
		}
		CLAIMS.computeIfAbsent(level.dimension(), k -> new HashMap<>()).merge(entity, scale, (a, b) -> a * b);
	}

	/** Зона-сфера: всем сущностям внутри — масштаб. Игроков — по желанию. */
	public static void claimZone(ServerLevel level, Vec3 center, double radius, float scale, boolean players) {
		AABB box = new AABB(center, center).inflate(radius);
		double r2 = radius * radius;
		for (Entity e : level.getEntities((Entity) null, box, e -> e.isAlive() && e.position().distanceToSqr(center) <= r2)) {
			if (!players && e instanceof Player) {
				continue;
			}
			claim(e, scale);
		}
	}

	/** Остановить время в сфере на {@code ticks}. {@code exempt} не замирает сам, и его снаряды тоже. */
	public static void stop(ServerLevel level, Vec3 center, double radius, int ticks, boolean players, @Nullable Entity exempt) {
		BUBBLES.add(new Bubble(level.dimension(), center, radius, level.getGameTime() + ticks, STOP, players,
			exempt == null ? null : exempt.getUUID()));
	}

	public static boolean inBubble(Entity entity) {
		for (Bubble b : BUBBLES) {
			if (b.level == entity.level().dimension() && entity.position().distanceToSqr(b.center) <= b.radius * b.radius) {
				return true;
			}
		}
		return false;
	}

	// ── конец тика: свести и разослать ──

	private static void commit(ServerLevel level) {
		long now = level.getGameTime();
		for (Iterator<Bubble> it = BUBBLES.iterator(); it.hasNext(); ) {
			Bubble b = it.next();
			if (b.until <= now) {
				it.remove();
				continue;
			}
			if (b.level != level.dimension()) {
				continue;
			}
			AABB box = new AABB(b.center, b.center).inflate(b.radius);
			double r2 = b.radius * b.radius;
			for (Entity e : level.getEntities((Entity) null, box, e -> e.isAlive() && e.position().distanceToSqr(b.center) <= r2)) {
				if (exempt(e, b)) {
					continue;
				}
				claim(e, b.scale);
			}
		}

		Map<Entity, Float> claims = CLAIMS.remove(level.dimension());
		Set<Entity> active = ACTIVE.computeIfAbsent(level.dimension(), k -> new HashSet<>());
		Set<Entity> next = new HashSet<>();
		if (claims != null) {
			for (Map.Entry<Entity, Float> c : claims.entrySet()) {
				Entity e = c.getKey();
				if (e.isRemoved()) {
					continue;
				}
				float s = c.getValue();
				if (s < IMMUNE_MIN && e.typeHolder().is(IMMUNE)) {
					s = IMMUNE_MIN;
				}
				s = Math.max(0.0F, Math.min(4.0F, s));
				if (Math.abs(s - 1.0F) < 0.01F) {
					continue;
				}
				next.add(e);
				set(e, s);
			}
		}
		for (Entity e : active) {
			if (!next.contains(e)) {
				set(e, 1.0F);
			}
		}
		active.clear();
		active.addAll(next);
	}

	private static boolean exempt(Entity e, Bubble b) {
		if (b.exempt == null) {
			return e instanceof Player && !b.players;
		}
		if (e.getUUID().equals(b.exempt)) {
			return true;
		}
		if (e instanceof Projectile p && p.getOwner() != null && p.getOwner().getUUID().equals(b.exempt)) {
			return true;
		}
		return e instanceof Player && !b.players;
	}

	private static void set(Entity e, float s) {
		Float old = e.getAttached(SCALE);
		boolean normal = s == 1.0F;
		if (normal ? old != null : (old == null || old != s)) {
			if (normal) {
				e.removeAttached(SCALE);
			} else {
				e.setAttached(SCALE, s);
			}
			if (e instanceof LivingEntity living) {
				applyAttributes(living, s);
			}
		}
	}

	/** Игрокам (и мобам заодно — для плавности ходьбы между пропусками) — модификаторы скорости. */
	private static void applyAttributes(LivingEntity living, float s) {
		boolean player = living instanceof Player;
		double speed = 0, jump = 0, gravity = 0, attack = 0;
		if (s <= 0.0F) {
			if (player) {
				speed = -1; jump = -1; gravity = -1; attack = -0.9;
			}
		} else if (s < 1.0F) {
			if (player) {
				speed = -0.4; jump = -0.25; gravity = -0.5; attack = -0.3;
			}
		} else if (s > 1.0F) {
			if (player) {
				speed = 0.4; attack = 0.5;
			}
		}
		modify(living, Attributes.MOVEMENT_SPEED, MOD_SPEED, speed);
		modify(living, Attributes.JUMP_STRENGTH, MOD_JUMP, jump);
		modify(living, Attributes.GRAVITY, MOD_GRAVITY, gravity);
		modify(living, Attributes.ATTACK_SPEED, MOD_ATTACK, attack);
		if (player && s <= 0.0F) {
			living.setDeltaMovement(Vec3.ZERO);
			if (living instanceof net.minecraft.server.level.ServerPlayer sp) {
				sp.syncVelocity = true;
			}
		}
	}

	private static void modify(LivingEntity living, Holder<Attribute> attribute, Identifier id, double amount) {
		AttributeInstance inst = living.getAttribute(attribute);
		if (inst == null) {
			return;
		}
		if (amount == 0) {
			inst.removeModifier(id);
		} else {
			inst.addOrUpdateTransientModifier(new AttributeModifier(id, amount, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
		}
	}
}
