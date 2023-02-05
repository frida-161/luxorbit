from pathlib import Path

import geopandas as gpd
from flask import abort, flash, redirect, render_template, request, session, url_for

from luxorbit import app, client
from luxorbit.auth import auth_required
from luxorbit.validator import async_validate


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/objectives")
def objectives():
    pois_gdf = gpd.read_file(Path(__file__).parent / Path("geo/pois.geojson"))
    pois_gdf = pois_gdf.to_crs("EPSG:4326")
    pois = [
        {
            "name": row["name"],
            "lat": row.geometry.coords[0][1],
            "lng": row.geometry.coords[0][0],
            "URL": row["URL"],
        }
        for idx, row in pois_gdf.iterrows()
    ]
    return render_template("objectives.html", pois=pois)


@app.route("/upload", methods=["GET", "POST"])
def upload_gpx():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file selected.")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No file selected.")
            return redirect(request.url)
        if file and file.filename.endswith(".gpx"):
            file_stream = file.read().decode("utf-8")
            task = async_validate.delay("upload", track_file_string=file_stream)
            return redirect(url_for("status", id=task.id, context="upload"))
        else:
            flash("Wrong filetype.")
            return redirect(request.url)
    else:
        return render_template("upload.html")


@app.route("/list/<context>")
@auth_required
def list_tracks(context):
    client.access_token = session.get("access_token")
    if context == "routes":
        tracks = client.get_routes(limit=10)
    elif context == "activities":
        tracks = client.get_activities(limit=10)
    else:
        return abort(422)
    return render_template("tracks.html", tracks=tracks, context=context)


@app.route("/activity/<context>/<id>")
@auth_required
def check_track(context, id):
    if context in ["routes", "activities"]:
        task = async_validate.delay(
            context, track_id=id, token=session.get("access_token")
        )
        return redirect(url_for("status", id=task.id, context=context))
    return abort(422)


@app.route("/status/<context>/<id>")
def status(context, id):
    task = async_validate.AsyncResult(id)
    if task.status in ("STARTED", "PENDING"):
        return render_template("waiting.html", task=task, context=context)
    elif task.status != "FAILURE":
        if "valid" in task.info:
            result = task.info
        return render_template("result.html", result=result)
