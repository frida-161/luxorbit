import fiona
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from luxorbit import app, client, db
from luxorbit.models import Challenge, GeometryType, Layer

challenge_bp = Blueprint("challenge", __name__, url_prefix="/challenge")
c_bp = Blueprint("c", __name__, url_prefix="/c")


@challenge_bp.route("/<int:challenge_id>")
@c_bp.route("/<string:challenge_name>")
def view(challenge_id: int = None, challenge_name: str = None):
    if challenge_id:
        challenge = db.session.query(Challenge).get(challenge_id)
    elif challenge_name:
        challenge = (
            db.session.query(Challenge).filter(Challenge.name == challenge_name).first()
        )

    if challenge:
        return render_template("challenge/view.html", challenge=challenge)

    abort(404)


@challenge_bp.route("/<int:challenge_id>/edit", methods=["GET", "POST"])
@challenge_bp.route("/create", methods=["GET", "POST"])
def edit(challenge_id=None):
    if challenge_id:
        challenge = db.session.query(Challenge).get(challenge_id)
        if not challenge:
            abort(404)
    else:
        challenge = Challenge()

    if request.method == "POST":
        if request.form.get("name").isalnum():
            challenge.name = request.form.get("name")
        else:
            flash("challenge name is not alphanumerical", "warning")
            return redirect(url_for("challenge.edit", challenge_id=challenge.id))

        challenge.roundtrip = request.form.get("roundtrip") is not None
        if request.form.get("distance"):
            challenge.required_distance = int(request.form.get("distance"))
        if request.form.get("elevation"):
            challenge.required_elevation = int(request.form.get("elevation"))

        db.session.add(challenge)
        db.session.commit()
        if request.url.endswith("/edit"):
            flash("Changes saved", "success")
        else:
            flash("Challenge created", "success")
        return redirect(url_for("challenge.edit", challenge_id=challenge.id))

    return render_template("challenge/edit.html", challenge=challenge)


@challenge_bp.route("<int:challenge_id>/add_layer", methods=["GET", "POST"])
def add_layer(challenge_id):
    challenge = db.session.query(Challenge).get(challenge_id)
    if not challenge:
        return abort(404)
    if request.method == "POST":
        if "file" not in request.files:
            flash("no file part")
            return redirect(url_for("challenge.add_layer"))

        file = request.files["file"]
        if file and file.filename.endswith(".geojson"):
            layer = Layer(name=file.filename)

            try:
                with fiona.open(file) as fi:
                    geom = fi.meta["schema"]["geometry"]
                    if geom.endswith("Polygon"):
                        layer.type = GeometryType.POLYGON
                    elif geom.endswith("Line"):
                        layer.type = GeometryType.LINE
                    elif geom.endswith("Point"):
                        layer.type = GeometryType.POINT
                    else:
                        flash(f"Unsupported geometry {geom}")
                        return redirect(
                            url_for("challenge.add_layer", challenge_id=challenge_id)
                        )
                    if not fi.crs.get("init") or fi.crs.get("init") != "epsg:4326":
                        flash("Unsupported Coordinate Reference System (use EPSG:4326)")
                        return redirect(
                            url_for("challenge.add_layer", challenge_id=challenge_id)
                        )
            except AttributeError:
                flash("Error reading GeoJSON")
                return redirect(url_for("challenge.add_layer"))

            file.seek(0)
            layer.file_blob = file.read()
            layer.challenge = challenge
            db.session.add(layer)
            db.session.commit()
            flash("added stuff")
            return redirect(url_for("layer.edit", layer_id=layer.id))
        else:
            flash("no selected file")
            return redirect(url_for("challenge.add_layer"))
    else:
        return render_template("layer/upload.html")
