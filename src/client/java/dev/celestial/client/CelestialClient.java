package dev.celestial.client;

import dev.celestial.client.dev.AutoPilot;
import dev.celestial.client.render.CelestialRenderers;
import net.fabricmc.api.ClientModInitializer;

public class CelestialClient implements ClientModInitializer {
	@Override
	public void onInitializeClient() {
		CelestialRenderers.init();
		SeraphWingsController.init();
		AutoPilot.init();
	}
}
