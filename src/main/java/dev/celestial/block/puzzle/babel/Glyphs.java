package dev.celestial.block.puzzle.babel;

/**
 * Смешение языков: 12 слов из рассказа о Вавилонской башне (Быт. 11:1–9), каждое записано четырьмя письмами —
 * 0 картинки (понятны глазу), 1 клинья, 2 руны, 3 вавилонское письмо (им набирают замок). Текстуры — tools/gen_babel.py.
 */
public final class Glyphs {
	public static final String[] WORDS = {"city", "tower", "heaven", "name", "brick", "tongue", "earth", "people", "one", "scatter", "top", "build"};
	public static final int COUNT = WORDS.length;
	public static final int SCRIPTS = 4;

	private Glyphs() {}
}
