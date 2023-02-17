from io import BytesIO

import fiona
from flask import Blueprint, abort, redirect, render_template, request, url_for

from luxorbit import app, client, db
from luxorbit.models import GeometryType, Layer
from luxorbit.strava.auth import auth_required
from luxorbit.validator import async_validate

layer_bp = Blueprint("layer", __name__, url_prefix="/layer")


@layer_bp.route("/<int:layer_id>", methods=["POST", "GET"])
def edit(layer_id):
    layer = db.session.query(Layer).get(layer_id)
    if layer:
        if request.method == "GET":
            layer_file = BytesIO(layer.file_blob)
            if request.url.endswith(".geojson"):
                return layer_file
            layer_schema = fiona.open(layer_file, driver="GeoJSON").meta.get("schema")
            if layer_schema and layer_schema.get("properties"):
                col_names = list(layer_schema.get("properties").keys())
            else:
                col_names = None
            return render_template("layer/edit.html", layer=layer, col_names=col_names)
        else:
            layer.name = request.form.get("name")
            layer.name_col = request.form.get("name_col")

            db.session.add(layer)
            db.session.commit()
            return redirect(url_for("layer.edit", layer_id=layer.id))
    else:
        abort(404)


@layer_bp.route("/<int:layer_id>.geojson")
def geojson(layer_id):
    layer = db.session.query(Layer).get(layer_id)
    if layer:
        return layer.file_blob
    abort(404)
