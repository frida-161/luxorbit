from luxorbit.auth import auth_required
from luxorbit.validator import async_validate_activity, async_validate_route
from luxorbit import client, app

from flask import session, render_template, redirect, url_for


@app.route("/")
@auth_required
def index():
    client.access_token = session.get("access_token")
    activities = client.get_activities()
    valid_activities = [
        a for a in activities
        if "vätternrundan" in a.name.lower()
    ]

    return render_template("activities.html", activities=valid_activities)


@app.route("/activity/<id>")
@auth_required
def activity(id):
    task = async_validate_activity.delay(id, session.get("access_token"))
    return redirect(url_for("status", id=task.id))


@app.route("/route/<id>")
@auth_required
def route(id):
    task = async_validate_route.delay(id, session.get("access_token"))
    return redirect(url_for("status", id=task.id))


@app.route("/status/<id>")
def status(id):
    task = async_validate_activity.AsyncResult(id)
    if task.status == "STARTED":
        return render_template("waiting.html", task=task)
    elif task.status != "FAILURE":
        if "valid" in task.info:
            result = task.info
        return render_template("success.html", result=result)


