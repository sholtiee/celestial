package dev.celestial.mech;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Сеть оборотов. Источники (пружина, котёл, разогнанный маховик) раз в {@link #PERIOD} тиков заявляют выход
 * ({@link #request}); в конце тика все заявки сводятся одним проходом: обход в ширину от каждой выходной грани раскручивает
 * детали ({@link MechBlock#SPIN}: 1 — по правилу правой руки вдоль положительной оси, 2 — против). Источник крутит «от себя»
 * (выход на восток — плюс по X, на запад — минус). Соосная передача сохраняет направление, зацепление шестерён меняет его.
 * Если в одну сеть два источника гонят вращение навстречу — сеть **заклинило**: ничего не крутится, из шестерён дым.
 * Деталь, которую не раскрутили, останавливается через {@link #HOLD} тиков.
 * Потребители (пресс, лифт, кузня) спрашивают {@link #driven}: смотрит ли на них вращающаяся деталь своей осью.
 */
public final class Gears {
	public static final int PERIOD = 4;
	private static final int HOLD = PERIOD + 3;
	private static final int MAX_NODES = 256;

	private record Request(BlockPos source, Direction out, int spin, boolean primary) {}

	private static final Map<ResourceKey<Level>, List<Request>> REQUESTS = new HashMap<>();
	/** Детали, раскрученные любым источником: позиция → до какого тика крутится. */
	private static final Map<ResourceKey<Level>, Map<BlockPos, Long>> SPINNING = new HashMap<>();
	/** То же, но только первичными источниками (маховик не должен раскручивать сам себя). */
	private static final Map<ResourceKey<Level>, Map<BlockPos, Long>> PRIMARY = new HashMap<>();
	/** Заклинившие детали (для отладки и сценариев): позиция → до какого тика. */
	private static final Map<ResourceKey<Level>, Map<BlockPos, Long>> JAMMED = new HashMap<>();

	private Gears() {}

	public static void init() {
		ServerTickEvents.END_LEVEL_TICK.register(Gears::endTick);
	}

	/** Направление «от себя» для выхода в сторону out: плюс вдоль положительной оси. */
	public static int spinFor(Direction out) {
		return out.getAxisDirection() == Direction.AxisDirection.POSITIVE ? 1 : 2;
	}

	/** Источник заявляет выход на этот тик (зовётся из тикера на тиках, кратных {@link #PERIOD}). */
	public static void request(ServerLevel level, BlockPos source, Direction out, int spin, boolean primary) {
		REQUESTS.computeIfAbsent(level.dimension(), k -> new ArrayList<>()).add(new Request(source.immutable(), out, spin, primary));
	}

	public static boolean primary(Level level, BlockPos pos) {
		return active(PRIMARY, level, pos);
	}

	public static boolean jammed(Level level, BlockPos pos) {
		return active(JAMMED, level, pos);
	}

	private static boolean active(Map<ResourceKey<Level>, Map<BlockPos, Long>> map, Level level, BlockPos pos) {
		Map<BlockPos, Long> m = map.get(level.dimension());
		Long until = m == null ? null : m.get(pos);
		return until != null && until > level.getGameTime();
	}

	/** Смотрит ли на блок вращающаяся деталь своей осью (работает и на клиенте — по состоянию блоков). */
	public static boolean driven(Level level, BlockPos pos) {
		for (Direction d : Direction.values()) {
			BlockState st = level.getBlockState(pos.relative(d));
			if (st.getBlock() instanceof Mech m && st.hasProperty(MechBlock.SPIN) && st.getValue(MechBlock.SPIN) > 0
				&& m.connects(st, d.getOpposite())) {
				return true;
			}
		}
		return false;
	}

	private static void endTick(ServerLevel level) {
		List<Request> reqs = REQUESTS.remove(level.dimension());
		if (reqs != null && !reqs.isEmpty()) {
			solve(level, reqs);
		}
		expire(level);
	}

	/** Свести заявки: обходы от каждого выхода, сети с противоречием — заклинены (система непересекающихся множеств по заявкам). */
	private static void solve(ServerLevel level, List<Request> reqs) {
		reqs.sort((a, b) -> Boolean.compare(b.primary, a.primary));  // первичные — первыми
		int n = reqs.size();
		int[] parent = new int[n];
		boolean[] jam = new boolean[n];
		for (int i = 0; i < n; i++) {
			parent[i] = i;
		}
		Map<BlockPos, Integer> spinOf = new HashMap<>();
		Map<BlockPos, Integer> owner = new HashMap<>();
		Set<BlockPos> sources = new HashSet<>();
		for (Request r : reqs) {
			sources.add(r.source);
		}
		for (int i = 0; i < n; i++) {
			Request r = reqs.get(i);
			BlockPos start = r.source.relative(r.out);
			BlockState s0 = level.getBlockState(start);
			if (!(s0.getBlock() instanceof Mech m0) || !m0.connects(s0, r.out.getOpposite())) {
				continue;
			}
			ArrayDeque<BlockPos> queue = new ArrayDeque<>();
			if (!visit(start, r.spin, i, spinOf, owner, parent, jam, queue)) {
				continue;
			}
			int count = 0;
			while (!queue.isEmpty() && count++ < MAX_NODES) {
				BlockPos p = queue.poll();
				BlockState st = level.getBlockState(p);
				if (!(st.getBlock() instanceof Mech m)) {
					continue;
				}
				int sp = spinOf.get(p);
				for (Direction d : Direction.values()) {
					BlockPos q = p.relative(d);
					if (sources.contains(q)) {
						continue;
					}
					int ns = -1;
					if (m.connects(st, d)) {
						BlockState qs = level.getBlockState(q);
						if (qs.getBlock() instanceof Mech qm && qm.connects(qs, d.getOpposite())) {
							ns = sp;
						}
					} else if (m.meshes(st) && d.getAxis() != m.axis(st)) {
						BlockState qs = level.getBlockState(q);
						if (qs.getBlock() instanceof Mech qm && qm.meshes(qs) && qm.axis(qs) == m.axis(st)) {
							ns = 3 - sp;
						}
					}
					if (ns > 0) {
						visit(q, ns, i, spinOf, owner, parent, jam, queue);
					}
				}
			}
		}
		long now = level.getGameTime();
		for (Map.Entry<BlockPos, Integer> e : owner.entrySet()) {
			int root = find(parent, e.getValue());
			BlockPos p = e.getKey();
			if (jam[root]) {
				JAMMED.computeIfAbsent(level.dimension(), k -> new HashMap<>()).put(p, now + HOLD);
				BlockState st = level.getBlockState(p);
				if (now % 20 < PERIOD && st.getBlock() instanceof Mech m && m.meshes(st)) {
					level.sendParticles(ParticleTypes.SMOKE, p.getX() + 0.5, p.getY() + 0.6, p.getZ() + 0.5, 2, 0.2, 0.2, 0.2, 0.01);
				}
				continue;
			}
			mark(level, p, spinOf.get(p), reqs.get(e.getValue()).primary);
		}
	}

	/** Посетить деталь: новая — в очередь; уже раскрученная другой заявкой — слить сети, при разном направлении — заклинило. */
	private static boolean visit(BlockPos q, int spin, int i, Map<BlockPos, Integer> spinOf, Map<BlockPos, Integer> owner,
		int[] parent, boolean[] jam, ArrayDeque<BlockPos> queue) {
		Integer had = spinOf.get(q);
		if (had == null) {
			spinOf.put(q, spin);
			owner.put(q, i);
			queue.add(q);
			return true;
		}
		int a = find(parent, i), b = find(parent, owner.get(q));
		if (a != b) {
			parent[a] = b;
			jam[b] |= jam[a];
		}
		if (had != spin) {
			jam[b] = true;
		}
		return false;
	}

	private static int find(int[] parent, int i) {
		while (parent[i] != i) {
			parent[i] = parent[parent[i]];
			i = parent[i];
		}
		return i;
	}

	/** Раскрутить одну деталь на {@link #HOLD} тиков. */
	public static void mark(ServerLevel level, BlockPos p, int spin, boolean primary) {
		long until = level.getGameTime() + HOLD;
		SPINNING.computeIfAbsent(level.dimension(), k -> new HashMap<>()).put(p, until);
		if (primary) {
			PRIMARY.computeIfAbsent(level.dimension(), k -> new HashMap<>()).put(p, until);
		}
		BlockState st = level.getBlockState(p);
		if (st.hasProperty(MechBlock.SPIN) && st.getValue(MechBlock.SPIN) != spin) {
			level.setBlock(p, st.setValue(MechBlock.SPIN, spin), Block.UPDATE_ALL);
		}
		if (primary && level.getBlockEntity(p) instanceof FlywheelBlockEntity fw) {
			fw.charge(level.getGameTime(), spin);
		}
	}

	private static void expire(ServerLevel level) {
		long now = level.getGameTime();
		for (Map<ResourceKey<Level>, Map<BlockPos, Long>> map : List.of(PRIMARY, JAMMED)) {
			Map<BlockPos, Long> m = map.get(level.dimension());
			if (m != null) {
				m.values().removeIf(t -> t <= now);
			}
		}
		Map<BlockPos, Long> spinning = SPINNING.get(level.dimension());
		if (spinning == null || spinning.isEmpty()) {
			return;
		}
		List<BlockPos> stop = new ArrayList<>();
		for (Iterator<Map.Entry<BlockPos, Long>> it = spinning.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<BlockPos, Long> e = it.next();
			if (e.getValue() <= now) {
				stop.add(e.getKey());
				it.remove();
			}
		}
		for (BlockPos p : stop) {
			if (!level.isLoaded(p)) {
				continue;
			}
			BlockState st = level.getBlockState(p);
			if (st.hasProperty(MechBlock.SPIN) && st.getValue(MechBlock.SPIN) != 0) {
				level.setBlock(p, st.setValue(MechBlock.SPIN, 0), Block.UPDATE_ALL);
			}
		}
	}
}
