package dev.celestial.data;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;

/** Сеть Небесных маяков мира: список точек телепорта во всех измерениях. */
public record BeaconNetwork(List<Beacon> beacons) {
	public record Beacon(String dimension, BlockPos pos, String name) {
		public static final Codec<Beacon> CODEC = RecordCodecBuilder.create(i -> i.group(
			Codec.STRING.fieldOf("dimension").forGetter(Beacon::dimension),
			BlockPos.CODEC.fieldOf("pos").forGetter(Beacon::pos),
			Codec.STRING.fieldOf("name").forGetter(Beacon::name)
		).apply(i, Beacon::new));
	}

	public static final BeaconNetwork EMPTY = new BeaconNetwork(List.of());
	public static final Codec<BeaconNetwork> CODEC = Beacon.CODEC.listOf().xmap(BeaconNetwork::new, BeaconNetwork::beacons);

	public BeaconNetwork with(Beacon beacon) {
		List<Beacon> copy = new ArrayList<>(without(beacon.dimension(), beacon.pos()).beacons());
		copy.add(beacon);
		return new BeaconNetwork(List.copyOf(copy));
	}

	public BeaconNetwork without(String dimension, BlockPos pos) {
		return new BeaconNetwork(beacons.stream().filter(b -> !(b.dimension().equals(dimension) && b.pos().equals(pos))).toList());
	}
}
