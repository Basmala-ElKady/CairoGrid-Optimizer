from __future__ import annotations

import logging
import numpy as np
import pandas as pd
import joblib
import os

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

from Backend.models.edge import Edge
from Backend.models.enums import TimePeriod

logger = logging.getLogger(__name__)

# config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "data", "traffic_model.pkl")

#time period encoding for ML features
_PERIOD_ORDER = {
    TimePeriod.MORNING_PEAK: 0,
    TimePeriod.AFTERNOON:    1,
    TimePeriod.EVENING_PEAK: 2,
    TimePeriod.NIGHT:        3,
}


# DATA LOADING 

def load_traffic_dataset():
    df = pd.read_csv("Backend/data/processed/traffic_flow.csv")

    rows = []

    for _, r in df.iterrows():
        road_id = r["RoadID"]

        flows =[
            r["Morning Peak(veh/h)"],
            r["Afternoon(veh/h)"],
            r["Evening Peak(veh/h)"],
            r["Night(veh/h)"]
        ]

        
        for i in range(2,len(flows)):


            rows.append([road_id,
                        flows[i-1],  # past 1
                        flows[i-2],  # past 2
                        flows[i]     # Target: future flow
                        ])


    return pd.DataFrame(rows, columns=[
        "edge_id",
        "lag_1_flow",
        "lag_2_flow",
        "target_flow"
    ])
# Service

class TrafficMLService:

    FEATURE_COLS = ["lag_1_flow", "lag_2_flow"]

    def __init__(self, graph):
        self.graph = graph
        self._is_trained = False


        self._pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=4,
                random_state=42
            ))
        ])

    # Training

    def train(self) -> "TrafficMLService":

        df = load_traffic_dataset()

        if df.empty:
            raise RuntimeError("Training dataset is empty. Check your data loading logic.")

        X = df[["lag_1_flow", "lag_2_flow"]].values
        y = df["target_flow"].values

        print(f"Training samples: {len(X)}")
        print("sample X:", X[:5])
        print("sample y:", y[:5])

        if len(X) == 0:
            raise RuntimeError("No training data available. Check your dataset.")
        
        self._pipeline.fit(X, y)
        self._is_trained = True

        return self


    def save_model(self, filepath: str = MODEL_PATH):
        if not self._is_trained:
            raise RuntimeError("Cannot save an untrained model.")
        
        joblib.dump(self._pipeline, filepath)
        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str = MODEL_PATH):
        if os.path.exists(filepath):
            self._pipeline = joblib.load(filepath)
            self._is_trained = True
            logger.info(f"Model loaded from {filepath}")
        else:
            logger.warning(f"No model found at {filepath}. Manual training required.")

    # Prediction
    # PREDICT NEXT FLOW 
    def predict_next_flow(self, edge):

        # Get flows from the actual flow_data attribute in TrafficProfile
        flows = list(edge.traffic.flow_data.values())

        if len(flows) < 2:
            return 0.0
        
        lag1 = flows[-1]
        lag2 = flows[-2]

        X = np.array([[lag1, lag2]])

        return float(self._pipeline.predict(X)[0])

    # CONGESTION 
    def predict_congestion(self, edge):
        next_flow = self.predict_next_flow(edge)
        capacity = edge.capacity or 1e-6

        return next_flow / capacity