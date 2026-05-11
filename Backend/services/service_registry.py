import os
from Backend.services.traffic_ml_service import TrafficMLService

# Private global variable to hold the model instance
_ml_instance = None

def get_ml_service(graph=None):
    """
    Returns the singleton ML service. 
    On the first call, it requires the 'graph' object to initialize.
    """
    global _ml_instance

    if _ml_instance is None:
        if graph is None:
            raise RuntimeError("ML Service must be initialized with a graph first!")

        # 1. Create the instance
        _ml_instance = TrafficMLService(graph)

        # 2. Define a robust path to the data folder
        # This points to Backend/data/traffic_model.pkl regardless of where you run the code
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "..", "data", "traffic_model.pkl")

        # 3. Load if exists, otherwise train and save
        if os.path.exists(model_path):
            _ml_instance.load_model(model_path)
        else:
            print("Model file not found. Training model for the first time...")
            _ml_instance.train()
            _ml_instance.save_model(model_path)

    return _ml_instance