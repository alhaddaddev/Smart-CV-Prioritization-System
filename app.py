import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename

from database import (
    init_db, add_job, get_all_jobs, get_job,
    add_cv, get_cvs_for_job, get_all_pool_cvs,
    attach_cv_to_job_by_id, delete_cv_by_filename,
    delete_job_by_id, update_job_cv_score
)

from utils.scorer import process_cv

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx", "png", "jpg", "jpeg"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = "change-this-secret"

init_db()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("jobs.html", jobs=get_all_jobs())

# ---------------- JOB DETAIL ----------------

@app.route("/job/<int:job_id>", methods=["GET", "POST"])
def job_detail(job_id):
    job = get_job(job_id)
    if not job:
        flash("Job not found", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "upload":
            files = request.files.getlist("cvs")

            for f in files:
                if f and allowed_file(f.filename):
                    filename = secure_filename(f.filename)
                    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

                    base, ext = os.path.splitext(filename)
                    i = 1
                    while os.path.exists(path):
                        filename = f"{base}_{i}{ext}"
                        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                        i += 1

                    f.save(path)

                    cv_id = add_cv(filename)
                    attach_cv_to_job_by_id(job_id, cv_id=cv_id)

            flash("CVs uploaded & attached", "success")
            return redirect(url_for("job_detail", job_id=job_id))

        elif action == "attach":
            filenames = request.form.getlist("existing_cvs")
            for name in filenames:
                attach_cv_to_job_by_id(job_id, filename=name)

            flash("CVs attached", "success")
            return redirect(url_for("job_detail", job_id=job_id))

    # Score CVs
    cvs = get_cvs_for_job(job_id)

    for cv in cvs:
        if cv["score"] is not None:
            continue
        
        path = os.path.join(app.config["UPLOAD_FOLDER"], cv["filename"])
        score, flags, insights = process_cv(path, job["description"])

        status = (
            "High" if score >= 75 else
            "Medium" if score >= 50 else
            "Low"
        )

        update_job_cv_score(
            job_id=job_id,
            cv_id=cv["id"],
            score=score,
            flags=flags,
            status=status,
            nlp_insights=insights
        )

    cvs = get_cvs_for_job(job_id)
    pool = get_all_pool_cvs()

    return render_template(
        "job_detail.html",
        job=job,
        cvs=cvs,
        unattached=pool
    )

# ---------------- CREATE JOB ----------------

@app.route("/create-job", methods=["POST"])
def create_job():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()

    if not title or not description:
        flash("Title and description required", "warning")
        return redirect(url_for("index"))

    add_job(title, description)
    flash("Job created", "success")
    return redirect(url_for("index"))

# ---------------- CV POOL ----------------

@app.route("/cvs", methods=["GET", "POST"])
def all_cvs():
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    if request.method == "POST":
        files = request.files.getlist("cvs_pool")

        for f in files:
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

                base, ext = os.path.splitext(filename)
                i = 1
                while os.path.exists(path):
                    filename = f"{base}_{i}{ext}"
                    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    i += 1

                f.save(path)
                add_cv(filename)

        flash("CVs uploaded to pool", "success")
        return redirect(url_for("all_cvs"))

    cvs = get_all_pool_cvs(date_from=date_from, date_to=date_to)

    return render_template(
        "cvs.html",
        cvs=cvs,
        date_from=date_from,
        date_to=date_to
    )

# ---------------- DELETE ----------------

@app.route("/delete-cv/<path:filename>", methods=["POST"])
def delete_cv(filename):
    delete_cv_by_filename(filename, upload_dir=UPLOAD_FOLDER)
    flash("CV deleted", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/delete-job/<int:job_id>", methods=["POST"])
def delete_job(job_id):
    delete_job_by_id(job_id)
    flash("Job deleted", "success")
    return redirect(url_for("index"))

# ---------------- FILE SERVE ----------------

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    app.run(debug=True)
