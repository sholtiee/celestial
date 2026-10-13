package dev.celestial.astral;

import dev.celestial.Celestial;
import dev.celestial.data.CelestialData;
import dev.celestial.data.PlayerData;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.Holder;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import org.jspecify.annotations.Nullable;

/**
 * Небесный покровитель — 4-я ветка Благодати. Собранный хор (решённый Звёздный диск) — запись Кодекса {@code choir:<id>};
 * выбранный покровитель — {@code patron:<id>} (одна за раз, меняется ПКМ по решённому диску). Благословение действует, пока хор — покровитель.
 * Ранг Благодати — число собранных хоров: Ангел … Херувим; Серафимом становится лишь выбравший «Поглотить» (финал).
 */
public final class Choirs {
	private static final Identifier MOD = Celestial.id("patron");
	private static final Identifier MOD2 = Celestial.id("patron_2");

	private Choirs() {}

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(Choirs::tick);
		// Серафимы: удары покровительствуемого поджигают
		ServerLivingEntityEvents.AFTER_DAMAGE.register((entity, source, base, taken, blocked) -> {
			if (taken > 0 && source.getEntity() instanceof ServerPlayer p && patron(CelestialData.get(p)) == Choir.SERAPHIM && entity != p) {
				entity.igniteForSeconds(4.0F);
			}
		});
	}

	public static boolean collected(PlayerData d, Choir c) {
		return d.knows("choir:" + c.id);
	}

	public static int count(PlayerData d) {
		int n = 0;
		for (Choir c : Choir.values()) {
			if (collected(d, c)) {
				n++;
			}
		}
		return n;
	}

	/** Ранг 0..8 по числу хоров; ранг Серафима (8) — только после «Поглотить». */
	public static int rank(PlayerData d) {
		int n = count(d);
		return d.knows("ending:consume") ? Choir.SERAPHIM.rank() : Math.min(n, Choir.CHERUBIM.rank());
	}

	public static @Nullable Choir patron(PlayerData d) {
		for (Choir c : Choir.values()) {
			if (d.knows("patron:" + c.id)) {
				return c;
			}
		}
		return null;
	}

	/** Сделать хор покровителем (если собран). */
	public static boolean setPatron(ServerPlayer p, Choir choir) {
		if (!collected(CelestialData.get(p), choir)) {
			return false;
		}
		CelestialData.update(p, d -> {
			PlayerData out = d;
			for (Choir c : Choir.values()) {
				out = out.withoutCodex("patron:" + c.id);
			}
			return out.withCodex("patron:" + choir.id);
		});
		apply(p);
		return true;
	}

	private static void tick(MinecraftServer server) {
		if (server.getTickCount() % 20 != 0) {
			return;
		}
		for (ServerPlayer p : server.getPlayerList().getPlayers()) {
			apply(p);
			Choir c = patron(CelestialData.get(p));
			if (c == Choir.SERAPHIM) {
				p.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 60, 0, true, false, true));
			} else if (c == Choir.THRONES && p.getHealth() < p.getMaxHealth() * 0.3F && p.level() instanceof ServerLevel level) {
				// Престолы: когда ты при смерти, время вокруг тянется (продлевается каждую секунду, пока здоровья мало)
				dev.celestial.chrono.TimeFlow.slowAround(level, p, 5.0, 21);
			}
		}
	}

	/** Чистота кристалла, которым настроен хор (0 — не настроен); см. StarCrystalItem. */
	public static int attunement(PlayerData d, Choir c) {
		int best = 0;
		for (String e : d.codex()) {
			if (e.startsWith("attune:" + c.id + ":")) {
				try {
					best = Math.max(best, Integer.parseInt(e.substring(("attune:" + c.id + ":").length())));
				} catch (NumberFormatException ignored) {
					// чужая запись — пропустить
				}
			}
		}
		return best;
	}

	/** Модификаторы атрибутов покровителя (снимаются, если покровитель другой или его нет); настройка кристаллом усиливает их. */
	public static void apply(ServerPlayer p) {
		Choir c = patron(CelestialData.get(p));
		double k = c == null ? 1.0 : 1.0 + attunement(CelestialData.get(p), c) / 100.0;
		set(p, Attributes.MOVEMENT_SPEED, MOD, c == Choir.ANGELS ? 0.10 * k : 0, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
		set(p, Attributes.SAFE_FALL_DISTANCE, MOD, c == Choir.ANGELS ? 6 * k : 0, AttributeModifier.Operation.ADD_VALUE);
		set(p, Attributes.MAX_HEALTH, MOD, c == Choir.ARCHANGELS ? 4 * k : 0, AttributeModifier.Operation.ADD_VALUE);
		set(p, Attributes.BLOCK_BREAK_SPEED, MOD, c == Choir.PRINCIPALITIES ? 0.25 * k : 0, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
		set(p, Attributes.ARMOR, MOD, c == Choir.POWERS ? 3 * k : 0, AttributeModifier.Operation.ADD_VALUE);
		set(p, Attributes.ARMOR_TOUGHNESS, MOD, c == Choir.POWERS ? 2 * k : 0, AttributeModifier.Operation.ADD_VALUE);
		set(p, Attributes.ATTACK_DAMAGE, MOD, c == Choir.VIRTUES ? 0.2 * k : 0, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
		set(p, Attributes.ATTACK_SPEED, MOD, c == Choir.DOMINIONS ? 0.15 * k : 0, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
		set(p, Attributes.LUCK, MOD, c == Choir.DOMINIONS ? 1 * k : 0, AttributeModifier.Operation.ADD_VALUE);
		set(p, Attributes.ATTACK_KNOCKBACK, MOD, c == Choir.CHERUBIM ? 1 * k : 0, AttributeModifier.Operation.ADD_VALUE);
		set(p, Attributes.KNOCKBACK_RESISTANCE, MOD2, c == Choir.CHERUBIM ? 0.5 * k : 0, AttributeModifier.Operation.ADD_VALUE);
	}

	private static void set(ServerPlayer p, Holder<Attribute> attr, Identifier id, double amount, AttributeModifier.Operation op) {
		AttributeInstance inst = p.getAttribute(attr);
		if (inst == null) {
			return;
		}
		AttributeModifier cur = inst.getModifier(id);
		if (cur != null && cur.amount() == amount) {
			return;
		}
		inst.removeModifier(id);
		if (amount != 0) {
			inst.addPermanentModifier(new AttributeModifier(id, amount, op));
		}
		if (attr == Attributes.MAX_HEALTH && p.getHealth() > p.getMaxHealth()) {
			p.setHealth(p.getMaxHealth());
		}
	}
}
