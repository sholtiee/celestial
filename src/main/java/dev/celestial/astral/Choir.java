package dev.celestial.astral;

import java.util.HashSet;
import java.util.Set;
import org.jspecify.annotations.Nullable;

/**
 * Девять ангельских хоров (чинов) — созвездия Астрала, от младшего к старшему. Рисунок — точки на поле 5×5 (x вправо, z вниз = на юг;
 * верх рисунка — север), центр (0,0) — сам Звёздный диск, он есть в каждом рисунке. Линии — пары индексов точек (только для рисунка в Кодексе).
 * Фаза Луны (0 — полнолуние … 7), в которую созвездие видно в Телескоп; у Серафимов −1 — их видно только из Астрала.
 */
public enum Choir {
	ANGELS("angels", 0, new int[][] {{0, 0}, {-1, -1}, {-2, -1}, {1, -1}, {2, -1}}, new int[][] {{0, 1}, {1, 2}, {0, 3}, {3, 4}}),
	ARCHANGELS("archangels", 1, new int[][] {{0, -2}, {0, -1}, {0, 0}, {0, 1}, {0, 2}, {-1, -1}, {1, -1}},
		new int[][] {{0, 1}, {1, 2}, {2, 3}, {3, 4}, {5, 1}, {1, 6}}),
	PRINCIPALITIES("principalities", 2, new int[][] {{0, 0}, {-2, 1}, {-2, -1}, {-1, 0}, {0, -2}, {1, 0}, {2, -1}, {2, 1}},
		new int[][] {{1, 2}, {2, 3}, {3, 4}, {4, 5}, {5, 6}, {6, 7}, {7, 1}, {0, 4}}),
	POWERS("powers", 3, new int[][] {{0, 0}, {0, -2}, {2, 0}, {0, 2}, {-2, 0}}, new int[][] {{1, 2}, {2, 3}, {3, 4}, {4, 1}, {0, 1}, {0, 3}}),
	VIRTUES("virtues", 4, new int[][] {{0, 0}, {-2, -2}, {-1, -1}, {1, 1}, {2, 2}, {2, -2}, {1, -1}, {-1, 1}, {-2, 2}},
		new int[][] {{1, 2}, {2, 0}, {0, 3}, {3, 4}, {5, 6}, {6, 0}, {0, 7}, {7, 8}}),
	DOMINIONS("dominions", 5, new int[][] {{0, 0}, {0, 2}, {0, 1}, {0, -1}, {-1, -2}, {1, -2}, {0, -2}},
		new int[][] {{1, 2}, {2, 0}, {0, 3}, {3, 6}, {6, 4}, {6, 5}}),
	THRONES("thrones", 6, new int[][] {{0, 0}, {-1, -2}, {1, -2}, {2, -1}, {2, 1}, {1, 2}, {-1, 2}, {-2, 1}, {-2, -1}},
		new int[][] {{1, 2}, {2, 3}, {3, 4}, {4, 5}, {5, 6}, {6, 7}, {7, 8}, {8, 1}, {0, 1}, {0, 4}, {0, 6}}),
	CHERUBIM("cherubim", 7, new int[][] {{0, 0}, {-2, -2}, {2, -2}, {2, 2}, {-2, 2}, {0, -1}},
		new int[][] {{0, 1}, {0, 2}, {0, 3}, {0, 4}, {0, 5}}),
	SERAPHIM("seraphim", -1, new int[][] {{0, 0}, {-2, -2}, {-2, 0}, {-2, 2}, {2, -2}, {2, 0}, {2, 2}},
		new int[][] {{0, 1}, {0, 2}, {0, 3}, {0, 4}, {0, 5}, {0, 6}});

	public final String id;
	public final int moonPhase;
	public final int[][] points;
	public final int[][] lines;

	Choir(String id, int moonPhase, int[][] points, int[][] lines) {
		this.id = id;
		this.moonPhase = moonPhase;
		this.points = points;
		this.lines = lines;
	}

	/** Ранг хора (0 — Ангелы … 8 — Серафимы). */
	public int rank() {
		return ordinal();
	}

	/** Смещения точек рисунка как множество ключей x*8+z (для сравнения с вставленными камнями). */
	public Set<Integer> cells() {
		Set<Integer> out = new HashSet<>();
		for (int[] p : points) {
			out.add(key(p[0], p[1]));
		}
		return out;
	}

	public static int key(int dx, int dz) {
		return (dx + 2) * 8 + (dz + 2);
	}

	public static @Nullable Choir byId(String id) {
		for (Choir c : values()) {
			if (c.id.equals(id)) {
				return c;
			}
		}
		return null;
	}

	/** Созвездие, видимое в Телескоп в эту фазу Луны (вне Астрала). */
	public static @Nullable Choir forMoonPhase(int phase) {
		for (Choir c : values()) {
			if (c.moonPhase == phase) {
				return c;
			}
		}
		return null;
	}
}
