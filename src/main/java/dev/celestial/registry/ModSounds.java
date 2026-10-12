package dev.celestial.registry;

import dev.celestial.Celestial;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.sounds.SoundEvent;

/** Свои звуки (синтезируются tools/gen_sounds.py, описаны в assets/celestial/sounds.json). */
public final class ModSounds {
	public static final Holder<SoundEvent> MUSIC_HEAVEN = registerHolder("music.heaven");
	public static final Holder<SoundEvent> MUSIC_SERAPH_BATTLE = registerHolder("music.seraph_battle");
	public static final Holder<SoundEvent> DISC_HEAVENLY_CHOIR = registerHolder("music_disc.heavenly_choir");
	public static final SoundEvent WING_FLAP = register("entity.wing_flap");
	public static final SoundEvent SPELL_CAST = register("spell.cast");
	public static final SoundEvent LIGHT_BOLT = register("spell.light_bolt");
	public static final SoundEvent METEOR_WHOOSH = register("meteor.whoosh");
	public static final SoundEvent METEOR_IMPACT = register("meteor.impact");
	public static final SoundEvent SHADOW_AMBIENT = register("entity.shadow.ambient");
	public static final SoundEvent SHADOW_BLINK = register("entity.shadow.blink");
	public static final SoundEvent CRYSTAL_BREAK = register("entity.seraph_crystal.break");
	public static final SoundEvent SERAPH_ROAR = register("entity.fallen_seraph.roar");
	public static final SoundEvent FADING_GROW = register("fading.grow");
	public static final SoundEvent TRIAL_START = register("trial.start");
	public static final net.minecraft.core.Holder<SoundEvent> MUSIC_DEVOURER_BATTLE = registerHolder("music.devourer_battle");
	public static final net.minecraft.core.Holder<SoundEvent> MUSIC_ABYSS = registerHolder("music.abyss");
	public static final SoundEvent DEVOURER_ROAR = register("entity.light_devourer.roar");
	public static final SoundEvent HUNTER_SCREECH = register("entity.blind_hunter.screech");
	public static final SoundEvent LIGHT_EATER_FEED = register("entity.light_eater.feed");
	public static final SoundEvent WORM_BITE = register("entity.deep_worm.bite");
	public static final net.minecraft.core.Holder<SoundEvent> MUSIC_ARCHON_BATTLE = registerHolder("music.archon_battle");
	public static final net.minecraft.core.Holder<SoundEvent> MUSIC_FROZEN = registerHolder("music.frozen");
	public static final SoundEvent ARCHON_ROAR = register("entity.frost_archon.roar");
	public static final SoundEvent ICE_CRACK = register("block.ice.crack");
	public static final SoundEvent GLACIER_SLIDE = register("block.glacier.slide");
	public static final SoundEvent ICE_BELL = register("block.ice_bell.ring");
	public static final SoundEvent SPIKE_RISE = register("entity.ice_spike.rise");
	public static final SoundEvent WOLF_HOWL = register("entity.ice_wolf.howl");
	public static final SoundEvent WOLF_HURT = register("entity.ice_wolf.hurt");
	public static final SoundEvent GUARDIAN_CRACK = register("entity.ice_guardian.crack");
	// Хроноград (волна 0.5) и финал
	public static final Holder<SoundEvent> MUSIC_CHRONOGRAD = registerHolder("music.chronograd");
	public static final Holder<SoundEvent> MUSIC_CLOCKMAKER_BATTLE = registerHolder("music.clockmaker_battle");
	public static final Holder<SoundEvent> MUSIC_FACELESS_BATTLE = registerHolder("music.faceless_battle");
	public static final SoundEvent CLOCK_TICK = register("block.clock.tick");
	public static final SoundEvent GEAR_WHIR = register("block.gear.whir");
	public static final SoundEvent STEAM_HISS = register("block.steam.hiss");
	public static final SoundEvent SENTRY_WIND = register("entity.clockwork_sentry.wind");
	public static final SoundEvent BEETLE_CHITTER = register("entity.winder_beetle.chitter");
	public static final SoundEvent DOLL_MUSIC_BOX = register("entity.brass_doll.music_box");
	public static final SoundEvent OPHANIM_HUM = register("entity.ophanim.hum");
	public static final SoundEvent OPHANIM_CHARGE = register("entity.ophanim.charge");
	public static final SoundEvent OPHANIM_BEAM = register("entity.ophanim.beam");
	public static final SoundEvent HORSE_WHINNY = register("entity.clockwork_horse.whinny");
	public static final SoundEvent CLOCKMAKER_STOP = register("entity.clockmaker.stop");
	public static final SoundEvent REWIND = register("block.rewind.rewind");
	public static final SoundEvent GLYPH_CLICK = register("block.glyph.click");

	private ModSounds() {}

	private static SoundEvent register(String name) {
		var id = Celestial.id(name);
		return Registry.register(BuiltInRegistries.SOUND_EVENT, id, SoundEvent.createVariableRangeEvent(id));
	}

	private static Holder<SoundEvent> registerHolder(String name) {
		var id = Celestial.id(name);
		return Registry.registerForHolder(BuiltInRegistries.SOUND_EVENT, id, SoundEvent.createVariableRangeEvent(id));
	}

	public static void init() {
	}
}
