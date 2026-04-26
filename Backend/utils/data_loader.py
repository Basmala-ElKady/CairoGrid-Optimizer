import pandas as pd
from typing import List
from models.node import Node
from models.edge import Edge
from models.enums import LocationType, TimePeriod

class DataLoader:
    @staticmethod
    def load_nodes(file_path: str, location_type: LocationType) -> List[Node]:
        """
        Parses location CSVs and returns a list of Node objects.
        """
        nodes = []
        try:
            df = pd.read_csv(file_path)
            # Standardize column headers
            df.columns = df.columns.str.strip().str.lower()

            for _, row in df.iterrows():
                nodes.append(Node(
                    node_id=str(row['id']),
                    name=row['name'],
                    node_type=location_type,
                    x=float(row.get('x-coordinate', 0)),
                    y=float(row.get('y-coordinate', 0)),
                    population=int(row.get('population', 0))
                ))
            return nodes
        except Exception as e:
            print(f"❌ Error loading nodes from {file_path}: {e}")
            return []

    @staticmethod
    def load_edges(roads_file: str, traffic_file: str) -> List[Edge]:
        """
        Merges road geometry with traffic profiles by normalizing IDs and splitting RoadID keys.
        """
        edges = []
        try:
            df_roads = pd.read_csv(roads_file)
            df_traffic = pd.read_csv(traffic_file)

            # Standardize headers for both DataFrames
            df_roads.columns = df_roads.columns.str.strip().str.lower()
            df_traffic.columns = df_traffic.columns.str.strip().str.lower()

            # --- DATA ALIGNMENT: Split 'roadid' (e.g., '1-3') into source and target columns ---
            traffic_split = df_traffic['roadid'].str.split('-', expand=True)
            df_traffic['fromid'] = traffic_split[0]
            df_traffic['toid'] = traffic_split[1]

            # Enforce string types to ensure perfect merging (handles alphanumeric IDs like 'F1')
            df_roads['fromid'] = df_roads['fromid'].astype(str)
            df_roads['toid'] = df_roads['toid'].astype(str)
            df_traffic['fromid'] = df_traffic['fromid'].astype(str)
            df_traffic['toid'] = df_traffic['toid'].astype(str)

            # Perform a left merge to attach traffic data to existing road segments
            merged_df = pd.merge(df_roads, df_traffic, on=['fromid', 'toid'], how='left')

            for _, row in merged_df.iterrows():
                # Encapsulate traffic volumes into a dictionary profile
                profile_data = {
                    TimePeriod.MORNING_PEAK: float(row.get('morning peak(veh/h)', 0)),
                    TimePeriod.AFTERNOON: float(row.get('afternoon(veh/h)', 0)),
                    TimePeriod.EVENING_PEAK: float(row.get('evening peak(veh/h)', 0)),
                    TimePeriod.NIGHT: float(row.get('night(veh/h)', 0))
                }

                # Construct Edge object with the consolidated data
                edge = Edge(
                    source_id=row['fromid'],
                    target_id=row['toid'],
                    distance=float(row.get('distance(km)', 0)),
                    capacity=int(row.get('current capacity(vehicles/hour)', 1000)),
                    condition=int(row.get('condition(1-10)', 5)),
                    traffic_profile=profile_data
                )
                edges.append(edge)
                
            return edges
        except Exception as e:
            print(f"❌ Error loading edges: {e}")
            return []