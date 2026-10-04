package dev.celestial.quest;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;

/** Какие поручения висят на доске сегодня: зависят от дня и места доски, одинаковы для всех игроков. */
public final class QuestPool {
	private record Template(Quest.Type type, String target, int min, int max, String reward, int rewardMin, int rewardMax, int rep) {}

	private static final List<Template> TEMPLATES = List.of(
		new Template(Quest.Type.KILL, "celestial:fallen_guardian", 4, 8, "celestial:starquartz", 4, 8, 8),
		new Template(Quest.Type.KILL, "celestial:winged_serpent", 3, 5, "celestial:starquartz", 4, 7, 8),
		new Template(Quest.Type.KILL, "celestial:storm_spirit", 2, 4, "celestial:etherite_ingot", 1, 2, 10),
		new Template(Quest.Type.KILL, "celestial:mimic", 1, 1, "celestial:rune_of_stars", 1, 1, 12),
		new Template(Quest.Type.KILL, "celestial:storm_elemental", 1, 1, "celestial:rune_of_light", 2, 2, 25),
		new Template(Quest.Type.BRING, "celestial:manna_berries", 12, 24, "celestial:starquartz", 3, 5, 6),
		new Template(Quest.Type.BRING, "celestial:cloud_fluff", 12, 24, "celestial:starquartz", 3, 5, 6),
		new Template(Quest.Type.BRING, "celestial:golden_fleece", 3, 6, "celestial:etherite_ingot", 1, 2, 10),
		new Template(Quest.Type.BRING, "celestial:sky_jelly", 3, 5, "celestial:rune_of_wind", 1, 1, 10),
		new Template(Quest.Type.BRING, "celestial:skywood_log", 24, 48, "celestial:starquartz", 4, 6, 6),
		new Template(Quest.Type.BRING, "celestial:raw_etherite", 6, 10, "celestial:rune_of_sky", 1, 1, 12),
		new Template(Quest.Type.EXPLORE, "celestial:sky_ruins", 1, 1, "celestial:starquartz", 6, 10, 10),
		new Template(Quest.Type.EXPLORE, "celestial:trial_tower", 1, 1, "celestial:etherite_ingot", 2, 3, 12),
		new Template(Quest.Type.EXPLORE, "celestial:beam_temple", 1, 1, "celestial:rune_of_light", 1, 1, 12),
		new Template(Quest.Type.EXPLORE, "celestial:cloud_castle", 1, 1, "celestial:etherite_ingot", 2, 4, 15),
		new Template(Quest.Type.EXPLORE, "celestial:airship_wreck", 1, 1, "celestial:starquartz", 8, 12, 12),
		new Template(Quest.Type.EXPLORE, "celestial:citadel", 1, 1, "celestial:seraph_feather", 3, 5, 20));

	public static final int PER_DAY = 3;

	private QuestPool() {}

	public static List<Quest> offers(long day, BlockPos board) {
		// сид только от дня: иначе передвинув доску на блок, получаешь новые поручения (обход «раз в день»)
		RandomSource random = RandomSource.create(day * 341873128712L);
		List<Quest> out = new ArrayList<>();
		List<Template> pool = new ArrayList<>(TEMPLATES);
		for (int i = 0; i < PER_DAY && !pool.isEmpty(); i++) {
			Template t = pool.remove(random.nextInt(pool.size()));
			int need = t.min() + random.nextInt(t.max() - t.min() + 1);
			int reward = t.rewardMin() + random.nextInt(t.rewardMax() - t.rewardMin() + 1);
			out.add(new Quest(t.type(), t.target(), need, 0, t.reward(), reward, t.rep()));
		}
		return out;
	}
}
