import pandas as pd
from typing import List
from models.node import Node
from models.edge import Edge
from models.enums import LocationType, TimePeriod

class DataLoader:
    @staticmethod
    def load_nodes(file_path: str, location_type: LocationType = LocationType.DISTRICT) -> List[Node]:
        """
        Parses location CSVs and returns a list of Node objects.
        """
        nodes = []
        try:
            df = pd.read_csv(file_path)
            # Standardize column headers
            df.columns = df.columns.str.strip().str.lower()

            for _, row in df.iterrows():
                # Enforce string type and clean float representations for IDs (e.g., '1.0' -> '1')
                raw_id = str(row['id']).replace('.0', '') if pd.notna(row.get('id')) else ""
                if not raw_id:
                    continue
                
                nodes.append(Node(
                    node_id=raw_id,
                    name=str(row.get('name', '')),
                    node_type=location_type,
                    x=float(row.get('x-coordinate', 0) if pd.notna(row.get('x-coordinate')) else 0),
                    y=float(row.get('y-coordinate', 0) if pd.notna(row.get('y-coordinate')) else 0),
                    population=int(float(row.get('population', 0)) if pd.notna(row.get('population')) else 0)
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
            if 'roadid' in df_traffic.columns:
                traffic_split = df_traffic['roadid'].astype(str).str.split('-', expand=True)
                df_traffic['fromid'] = traffic_split[0]
                if traffic_split.shape[1] > 1:
                    df_traffic['toid'] = traffic_split[1]
                else:
                    df_traffic['toid'] = ""

            # Helper to strip '.0' from float-parsed IDs, enforcing pure string
            def clean_id(series):
                return series.astype(str).str.replace(r'\.0$', '', regex=True)

            # Enforce string types to ensure perfect merging (handles alphanumeric IDs like 'F1')
            df_roads['fromid'] = clean_id(df_roads['fromid'])
            df_roads['toid'] = clean_id(df_roads['toid'])
            df_traffic['fromid'] = clean_id(df_traffic['fromid'])
            df_traffic['toid'] = clean_id(df_traffic['toid'])

            # Perform a left merge to attach traffic data to existing road segments
            merged_df = pd.merge(df_roads, df_traffic, on=['fromid', 'toid'], how='left')

            for _, row in merged_df.iterrows():
                # Encapsulate traffic volumes into a dictionary profile, safely handling NaNs
                profile_data = {
                    TimePeriod.MORNING_PEAK: float(row.get('morning peak(veh/h)', 0) if pd.notna(row.get('morning peak(veh/h)')) else 0),
                    TimePeriod.AFTERNOON: float(row.get('afternoon(veh/h)', 0) if pd.notna(row.get('afternoon(veh/h)')) else 0),
                    TimePeriod.EVENING_PEAK: float(row.get('evening peak(veh/h)', 0) if pd.notna(row.get('evening peak(veh/h)')) else 0),
                    TimePeriod.NIGHT: float(row.get('night(veh/h)', 0) if pd.notna(row.get('night(veh/h)')) else 0)
                }

                # Construct Edge object with the consolidated data
                edge = Edge(
                    source_id=row['fromid'],
                    target_id=row['toid'],
                    distance=float(row.get('distance(km)', 0) if pd.notna(row.get('distance(km)')) else 0),
                    capacity=int(float(row.get('current capacity(vehicles/hour)', 1000)) if pd.notna(row.get('current capacity(vehicles/hour)')) else 1000),
                    condition=int(float(row.get('condition(1-10)', 5)) if pd.notna(row.get('condition(1-10)')) else 5),
                    traffic_profile=profile_data
                )
                edges.append(edge)
                
            return edges
        except Exception as e:
            print(f"❌ Error loading edges: {e}")
            return []