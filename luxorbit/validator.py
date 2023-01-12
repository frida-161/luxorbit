from pathlib import Path
from shapely.geometry import Point, Polygon
from shapely.ops import transform
import pyproj
import requests
import geopandas as gpd
import fiona

from luxorbit import client, celery

vaettern = Polygon([ [ 15.049409984586353, 58.548337722745224 ], [ 15.049925559335811, 58.54797163111057 ], [ 14.933019066862725, 58.476143636129414 ], [ 14.878968731212906, 58.479609012416851 ], [ 14.780115691878537, 58.458773726405404 ], [ 14.687773680269547, 58.346276972274936 ], [ 14.548658560831695, 58.08655467128559 ], [ 14.303478893295402, 57.932625258170972 ], [ 14.255269200949423, 57.81746663927602 ], [ 14.176255808236153, 57.828376232387235 ], [ 14.142074097218606, 57.908412633933203 ], [ 14.163732666698147, 57.968734263707205 ], [ 14.277101274594303, 58.276653866639201 ], [ 14.30554797736054, 58.322049133128587 ], [ 14.402743660340086, 58.367108971295494 ], [ 14.386788296267168, 58.431242350245256 ], [ 14.470793223308322, 58.465057121284602 ], [ 14.4750810562056, 58.519535708911661 ], [ 14.534810261966788, 58.530065764088356 ], [ 14.57453943885252, 58.647354052600129 ], [ 14.739750098955959, 58.723906745978702 ], [ 14.749680919995058, 58.728491878390145 ], [ 14.851502454568214, 58.787908166315916 ], [ 14.847382654509151, 58.792233613725969 ], [ 14.896065157686051, 58.819253889686053 ], [ 15.00325756918223, 58.80011799341689 ], [ 14.961465449457791, 58.717650153410808 ], [ 14.934920780219183, 58.632057626127143 ], [ 14.908452291104032, 58.590753415976181 ], [ 14.991627216008753, 58.589333586916368 ], [ 15.049409984586353, 58.548337722745224 ] ])

@celery.task(bind=True)
def async_validate_route(self, id, token):
    self.update_state(state="STARTED")

    client.access_token = token
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        f"https://www.strava.com/api/v3/routes/{id}/export_gpx",
        headers=headers
    )

    valid = False
    reasons = []
    if resp.status_code == 200:
        # Check Cantons/Countries
        cantons_gdf = gpd.read_file(
            Path(__file__).parent / Path("geo/cantons.geojson")
        )

        with fiona.BytesCollection(bytes(resp.content), layer="tracks") as f:
            crs = f.crs
            tracks_gdf = gpd.GeoDataFrame.from_features(f, crs=crs)
            tracks_gdf_reproj = tracks_gdf.to_crs(cantons_gdf.crs)

        missing_cantons = cantons_gdf[
            cantons_gdf.intersects(tracks_gdf_reproj.geometry[0]) == False
        ]
        if not missing_cantons.empty:
            reasons.append((
                "Your track is missing the following areas: "
                f"{', '.join(missing_cantons.CANTON)}."
            ))

        # Check POIs
        pois_gdf = gpd.read_file(
            Path(__file__).parent / Path("geo/pois.geojson")
        )
        missing_pois = pois_gdf[
            pois_gdf.distance(tracks_gdf_reproj.geometry[0]) > 100
        ]
        if not missing_pois.empty:
            reasons.append((
                "Your track is missing the following POIs: "
                f"{', '.join(missing_pois.name)}"
            ))
        
        # Check if start point is near end point
        first_point = Point(tracks_gdf_reproj.geometry[0].geoms[0].coords[0])
        last_point = Point(tracks_gdf_reproj.geometry[0].geoms[0].coords[-1])
        if last_point.distance(first_point) > 100:
            reasons.append("Start and Finish are to far away from each other")
        
    else:
        reasons.append("Could not get track.")
    
    valid = not reasons

    return {"valid": valid, "reasons": reasons}


@celery.task(bind=True)
def async_validate_activity(self, id, token):
    self.update_state(state="STARTED")

    client.access_token = token
    types = ["latlng", "distance", "time"]
    streams = client.get_activity_streams(id, types=types)
    start_wgs84 = Point(streams["latlng"].data[0])
    end_wgs84 = Point(streams["latlng"].data[-1])

    project = pyproj.Transformer.from_crs(
        pyproj.CRS("EPSG:4326"),
        pyproj.CRS("EPSG:25832"),
        always_xy=True).transform

    start_utm = transform(project, start_wgs84)
    end_utm = transform(project, end_wgs84)
    distance = start_utm.distance(end_utm)

    vaettern_ = transform(lambda x, y: (y, x), vaettern)

    counter = 0
    for data_point in streams["latlng"].data:
        if vaettern_.contains(Point(data_point)):
            counter += 1

    percentage = 1 - counter / len(streams["latlng"].data)

    valid = distance < 1000 and percentage > 0.9

    return {"valid": valid, "distance": distance, "percentage": percentage, "point": str(start_wgs84)}
