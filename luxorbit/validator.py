from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, Point

from luxorbit import celery, client


@celery.task(bind=True)
def async_validate(self, context, track_id, token):
    self.update_state(state="STARTED")
    client.access_token = token

    valid = False
    reasons = []
    cantons_gdf = gpd.read_file(Path(__file__).parent / Path("geo/cantons.geojson"))

    if context == "routes":
        streams = client.get_route_streams(track_id)
    elif context == "activities":
        streams = client.get_activity_streams(track_id, types=["latlng"])
    else:
        return {"valid": False, "reasons": ["wrong context!"]}

    # reproject track
    track_line = LineString(
        [(coord[1], coord[0]) for coord in streams.get("latlng").data]
    )
    track_gdf = gpd.GeoDataFrame({"geometry": [track_line]}, crs="EPSG:4326")
    track_gdf = track_gdf.to_crs(cantons_gdf.crs)
    track_line = track_gdf.geometry[0]

    # Check Cantons/Countries
    missing_cantons = cantons_gdf[cantons_gdf.intersects(track_line) == False]
    if not missing_cantons.empty:
        reasons.append(
            (
                "Your track is missing the following areas: "
                f"{', '.join(missing_cantons.CANTON)}."
            )
        )

    # Check POIs
    pois_gdf = gpd.read_file(Path(__file__).parent / Path("geo/pois.geojson"))
    missing_pois = pois_gdf[pois_gdf.distance(track_line) > 100]
    if not missing_pois.empty:
        reasons.append(
            (
                "Your track is missing the following POIs: "
                f"{', '.join(missing_pois.name)}"
            )
        )

    # Check if start point is near end point
    first_point = Point(track_line.coords[0])
    last_point = Point(track_line.coords[-1])
    if last_point.distance(first_point) > 100:
        reasons.append("Start and Finish are to far away from each other")

    valid = not reasons

    return {
        "valid": valid,
        "reasons": reasons,
        "context": context,
    }
