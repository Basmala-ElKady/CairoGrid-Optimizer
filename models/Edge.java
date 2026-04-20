package models;

import java.util.HashMap;
import java.util.Map;

public class Edge {

    private final Node source;
    private final Node destination;
    private final double distance;
    private final int capacity;
    private final int conditionScore;
    private final Map<String, Integer> trafficData;

    public Edge(Node source, Node destination, double distance,
            int capacity, int conditionScore,
            Map<String, Integer> trafficData) {

        this.source = source;
        this.destination = destination;
        this.distance = distance;
        this.capacity = capacity;
        this.conditionScore = conditionScore;
        this.trafficData = trafficData != null ? new HashMap<>(trafficData) : new HashMap<>();
    }

    public Node getSource() {
        return source;
    }

    public Node getDestination() {
        return destination;
    }

    public double getDistance() {
        return distance;
    }

    public int getCapacity() {
        return capacity;
    }

    public int getConditionScore() {
        return conditionScore;
    }

    public Map<String, Integer> getTrafficData() {
        return new HashMap<>(trafficData);
    }

    public int getTrafficVolume(String period) {
        return trafficData.getOrDefault(period.toLowerCase(), 0);
    }

    public double getTravelTime(String period) {

        int traffic = getTrafficVolume(period);

        double speedFactor = (capacity - traffic) / (double) capacity;

        if (speedFactor <= 0)
            speedFactor = 0.1;

        return distance / speedFactor;
    }

    @Override
    public String toString() {
        return source.getId() + " -> " + destination.getId();
    }
}