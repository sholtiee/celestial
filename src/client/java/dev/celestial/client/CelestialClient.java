package dev.celestial.client;

import dev.celestial.client.dev.AutoPilot;
import net.fabricmc.api.ClientModInitializer;

public class CelestialClient implements ClientModInitializer {
	@Override
	public void onInitializeClient() {
		AutoPilot.init();
	}
}
