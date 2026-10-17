"""
CRADLE Accessibility & Road Network Module
Constructs Chennai road network topology using NetworkX, computes Dijkstra-based travel times
across road hierarchies, and generates 5, 10, and 15-minute service area catchments.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiPolygon
from shapely.ops import unary_union
import networkx as nx

import config


class RoadNetworkAccessibility:
    """
    Simulates Chennai arterial road network graph with speed hierarchies,
    computes travel time matrices, and generates multi-tier isochrone service areas.
    """

    def __init__(self, road_speeds: Optional[Dict[str, float]] = None):
        self.road_speeds = road_speeds or config.ROAD_SPEEDS.copy()
        self.graph = nx.Graph()
        self._init_chennai_network()

    def _init_chennai_network(self):
        """
        Initializes a topological road network model connecting Chennai zones and key corridors:
        - NH 16 (GNT Road / North Corridor)
        - NH 48 (Poonamallee High Road / West Corridor)
        - NH 32 (GST Road / Southwest Corridor)
        - Rajiv Gandhi Salai (OMR / IT Corridor)
        - East Coast Road (ECR / Coastal Corridor)
        - Inner Ring Road (Jawaharlal Nehru Road)
        - Anna Salai (Mount Road / Central Spine)
        """
        key_nodes = {
            "Central": (13.0827, 80.2707),
            "Royapuram": (13.1143, 80.2941),
            "Tondiarpet": (13.1310, 80.2882),
            "Tiruvottiyur": (13.1622, 80.3011),
            "Manali": (13.1667, 80.2600),
            "Madhavaram": (13.1489, 80.2314),
            "Anna_Nagar": (13.0850, 80.2101),
            "Ambattur": (13.1143, 80.1548),
            "Thiru_Vi_Ka": (13.1075, 80.2396),
            "Kodambakkam": (13.0520, 80.2240),
            "Teynampet": (13.0405, 80.2504),
            "Valasaravakkam": (13.0403, 80.1723),
            "Alandur": (13.0034, 80.2015),
            "Adyar": (13.0012, 80.2565),
            "Perungudi": (12.9654, 80.2461),
            "Sholinganallur": (12.9010, 80.2279),
            "Tambaram": (12.9249, 80.1278),
            "Poonamallee": (13.0490, 80.0880),
        }

        # Add nodes with lat/lon attributes
        for name, (lat, lon) in key_nodes.items():
            self.graph.add_node(name, lat=lat, lon=lon, pos=(lon, lat))

        # Add road corridor edges with hierarchy and realistic distances
        corridors = [
            # Central Spine (Anna Salai)
            ("Central", "Teynampet", "primary", 5.2),
            ("Teynampet", "Adyar", "primary", 5.5),
            ("Teynampet", "Alandur", "primary", 6.8),
            ("Alandur", "Tambaram", "trunk", 11.0),
            # North Corridor
            ("Central", "Royapuram", "primary", 3.8),
            ("Royapuram", "Tondiarpet", "secondary", 2.6),
            ("Tondiarpet", "Tiruvottiyur", "trunk", 4.5),
            ("Central", "Thiru_Vi_Ka", "secondary", 4.2),
            ("Thiru_Vi_Ka", "Madhavaram", "primary", 5.1),
            ("Madhavaram", "Manali", "secondary", 4.8),
            ("Tiruvottiyur", "Manali", "secondary", 5.2),
            # West Corridor
            ("Central", "Anna_Nagar", "primary", 7.0),
            ("Anna_Nagar", "Ambattur", "trunk", 6.5),
            ("Ambattur", "Poonamallee", "trunk", 8.2),
            ("Anna_Nagar", "Kodambakkam", "secondary", 5.0),
            ("Kodambakkam", "Valasaravakkam", "secondary", 6.0),
            ("Valasaravakkam", "Poonamallee", "primary", 9.0),
            ("Valasaravakkam", "Alandur", "secondary", 5.8),
            # South / OMR / ECR
            ("Adyar", "Perungudi", "trunk", 4.6),
            ("Perungudi", "Sholinganallur", "trunk", 7.5),
            ("Alandur", "Perungudi", "secondary", 5.9),
            ("Sholinganallur", "Tambaram", "primary", 12.0),
            # Ring connectors
            ("Anna_Nagar", "Thiru_Vi_Ka", "secondary", 4.0),
            ("Kodambakkam", "Teynampet", "secondary", 3.2),
        ]

        for u, v, rtype, dist_km in corridors:
            speed = self.road_speeds.get(rtype, self.road_speeds["default"])
            travel_time_min = (dist_km / speed) * 60.0
            self.graph.add_edge(u, v, road_type=rtype, distance_km=dist_km, travel_time_min=travel_time_min)

    def find_nearest_network_node(self, lat: float, lon: float) -> str:
        """Finds closest node in the road network graph to a geographic coordinate."""
        best_node = None
        min_dist_sq = float("inf")
        for node, data in self.graph.nodes(data=True):
            d2 = (data["lat"] - lat) ** 2 + (data["lon"] - lon) ** 2
            if d2 < min_dist_sq:
                min_dist_sq = d2
                best_node = node
        return best_node

    def compute_travel_time(self, origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> float:
        """
        Computes estimated driving travel time in minutes combining:
        1. Access time to road network node (local road 20 km/h)
        2. Shortest network route on graph
        3. Egress time from destination node
        """
        orig_node = self.find_nearest_network_node(origin_lat, origin_lon)
        dest_node = self.find_nearest_network_node(dest_lat, dest_lon)

        # Access distance in km (approx 1 deg ~ 111 km)
        o_data = self.graph.nodes[orig_node]
        access_dist = np.hypot((o_data["lat"] - origin_lat) * 111.0, (o_data["lon"] - origin_lon) * 105.0)
        access_time = (access_dist / 20.0) * 60.0

        d_data = self.graph.nodes[dest_node]
        egress_dist = np.hypot((d_data["lat"] - dest_lat) * 111.0, (d_data["lon"] - dest_lon) * 105.0)
        egress_time = (egress_dist / 20.0) * 60.0

        try:
            network_time = nx.shortest_path_length(
                self.graph, source=orig_node, target=dest_node, weight="travel_time_min"
            )
        except nx.NetworkXNoPath:
            # Fallback direct distance with winding factor 1.4
            direct_dist = np.hypot((dest_lat - origin_lat) * 111.0, (dest_lon - origin_lon) * 105.0) * 1.4
            return (direct_dist / 25.0) * 60.0

        return round(access_time + network_time + egress_time, 1)

    def calculate_travel_time_matrix(
        self,
        origins_gdf: gpd.GeoDataFrame,
        destinations_gdf: gpd.GeoDataFrame,
    ) -> np.ndarray:
        """
        Computes travel time matrix (minutes) from each origin to each destination.
        """
        times = np.zeros((len(origins_gdf), len(destinations_gdf)))

        orig_centroids = origins_gdf.geometry.centroid
        dest_coords = [(g.y, g.x) for g in destinations_gdf.geometry]

        for i, o_geom in enumerate(orig_centroids):
            for j, (d_lat, d_lon) in enumerate(dest_coords):
                times[i, j] = self.compute_travel_time(o_geom.y, o_geom.x, d_lat, d_lon)

        return times

    def generate_isochrones(
        self,
        center_lat: float,
        center_lon: float,
        time_thresholds_min: List[int] = [5, 10, 15],
    ) -> gpd.GeoDataFrame:
        """
        Generates 5, 10, and 15-minute travel-time isochrone polygons
        around a center coordinate using network travel reach.
        """
        center_node = self.find_nearest_network_node(center_lat, center_lon)
        lengths = nx.single_source_dijkstra_path_length(self.graph, source=center_node, weight="travel_time_min")

        isochrone_polygons = []
        isochrone_meta = []

        # Convert travel time reach to approximate spatial polygons in UTM
        center_pt_utm = gpd.GeoDataFrame(
            geometry=[Point(center_lon, center_lat)], crs=config.CRS_GEO
        ).to_crs(config.CRS_PROJ).geometry.iloc[0]

        for t_min in time_thresholds_min:
            # Reached nodes within t_min
            reached = [node for node, time in lengths.items() if time <= t_min]
            pts = [Point(center_lon, center_lat)]
            for node in reached:
                nd = self.graph.nodes[node]
                pts.append(Point(nd["lon"], nd["lat"]))

            # Create buffered convex hull representing network service area
            pts_gdf = gpd.GeoDataFrame(geometry=pts, crs=config.CRS_GEO).to_crs(config.CRS_PROJ)
            # Speed buffer: 25 km/h * (t_min / 60) * 1000m * winding_factor
            buffer_dist = max(1000, (25.0 * (t_min / 60.0) * 1000) * 0.75)
            hull = pts_gdf.geometry.unary_union.convex_hull.buffer(buffer_dist)

            iso_gdf = gpd.GeoDataFrame(geometry=[hull], crs=config.CRS_PROJ).to_crs(config.CRS_GEO)
            isochrone_polygons.append(iso_gdf.geometry.iloc[0])
            isochrone_meta.append({
                "Travel_Time_Min": t_min,
                "Service_Area_Tier": f"{t_min} Minutes",
                "Description": f"Accessible within {t_min} min drive",
            })

        return gpd.GeoDataFrame(isochrone_meta, geometry=isochrone_polygons, crs=config.CRS_GEO)
