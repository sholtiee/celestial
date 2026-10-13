package dev.celestial.client;

import dev.celestial.network.WorldStatePayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

/** Что клиент знает о мире: стадия Угасания и акт саги (приходят с сервера). */
public final class ClientState {
	private static int fading;
	private static int act;
	private static boolean fadingEnabled = true;
	private static String ending = "";

	private ClientState() {}

	public static void init() {
		ClientPlayNetworking.registerGlobalReceiver(WorldStatePayload.TYPE, (payload, context) -> {
			fading = payload.fading();
			act = payload.act();
			fadingEnabled = payload.fadingEnabled();
			ending = payload.ending();
		});
		// с сервера без мода (или до первого пакета) — исходное состояние, иначе небо «Поглотить» и Угасание тянулись бы из прошлого мира
		net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> {
			fading = 0;
			act = 0;
			fadingEnabled = true;
			ending = "";
		});
	}

	/** Действующая стадия Угасания с учётом правила игры. */
	public static int fading() {
		return fadingEnabled ? fading : 0;
	}

	public static int act() {
		return act;
	}

	/** Выбранная концовка Саги: "", kindle, consume, name. */
	public static String ending() {
		return ending;
	}
}
