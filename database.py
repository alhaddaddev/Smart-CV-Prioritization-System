import sqlite3
import json
import os

DB_PATH = "cv_data.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    if not os.path.exists(DB_PATH):
        open(DB_PATH, "a").close()

    conn = get_conn()
    cur = conn.cursor()

    # Jobs Table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # CVs Table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS cvs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            upload_time TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Job-CVs (job specific data)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS job_cvs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            cv_id INTEGER,
            score REAL,
            flags TEXT,
            status TEXT,
            nlp_insights TEXT,
            attached_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(job_id, cv_id)
        )
        """
    )

    conn.commit()
    conn.close()

# ---------------- JOBS ----------------

def add_job(title, description):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO jobs (title, description) VALUES (?, ?)",
        (title, description),
    )
    conn.commit()
    conn.close()


def get_all_jobs():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, created_at FROM jobs ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "created_at": r[2]} for r in rows]


def get_job(job_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, description FROM jobs WHERE id = ?", (job_id,)
    )
    r = cur.fetchone()
    conn.close()
    if not r:
        return None
    return {"id": r[0], "title": r[1], "description": r[2]}


def delete_job_by_id(job_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM job_cvs WHERE job_id = ?", (job_id,))
    cur.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()

# ---------------- CVS ----------------

def add_cv(filename):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO cvs (filename) VALUES (?)",
            (filename,),
        )
    except sqlite3.IntegrityError:
        pass

    conn.commit()
    cv_id = cur.execute(
        "SELECT id FROM cvs WHERE filename = ?", (filename,)
    ).fetchone()[0]
    conn.close()
    return cv_id

def attach_cv_to_job_by_id(job_id, cv_id=None, filename=None):
    conn = get_conn()
    cur = conn.cursor()

    if cv_id is None and filename:
        cur.execute("SELECT id FROM cvs WHERE filename = ?", (filename,))
        r = cur.fetchone()
        if not r:
            conn.close()
            return False
        cv_id = r[0]

    cur.execute(
        "INSERT OR IGNORE INTO job_cvs (job_id, cv_id) VALUES (?, ?)",
        (job_id, cv_id),
    )

    conn.commit()
    conn.close()
    return True

def update_job_cv_score(job_id, cv_id, score, flags, status, nlp_insights):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE job_cvs
        SET score=?, flags=?, status=?, nlp_insights=?
        WHERE job_id=? AND cv_id=?
        """,
        (
            score,
            json.dumps(flags),
            status,
            json.dumps(nlp_insights),
            job_id,
            cv_id,
        ),
    )
    conn.commit()
    conn.close()

def _row_to_cv(r):
    def load(j):
        try:
            return json.loads(j) if j else []
        except Exception:
            return []

    return {
        "id": r[0],
        "filename": r[1],
        "score": r[2],
        "flags": load(r[3]),
        "status": r[4],
        "nlp_insights": load(r[5]),
        "upload_time": r[6],
    }

def get_cvs_for_job(job_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            c.id, c.filename, jc.score, jc.flags, jc.status, jc.nlp_insights, c.upload_time
        FROM cvs c
        JOIN job_cvs jc ON jc.cv_id = c.id
        WHERE jc.job_id = ?
        ORDER BY jc.score DESC
        """,
        (job_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [_row_to_cv(r) for r in rows]

def get_all_pool_cvs(date_from=None, date_to=None):
    conn = get_conn()
    cur = conn.cursor()

    query = """
        SELECT id, filename, NULL, NULL, NULL, NULL, upload_time
        FROM cvs
        WHERE 1=1
    """
    params = []

    if date_from:
        query += " AND date(upload_time) >= date(?)"
        params.append(date_from)

    if date_to:
        query += " AND date(upload_time) <= date(?)"
        params.append(date_to)

    query += " ORDER BY upload_time DESC"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [_row_to_cv(r) for r in rows]

def delete_cv_by_filename(filename, upload_dir=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM cvs WHERE filename = ?", (filename,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return False

    cv_id = r[0]
    cur.execute("DELETE FROM job_cvs WHERE cv_id = ?", (cv_id,))
    cur.execute("DELETE FROM cvs WHERE id = ?", (cv_id,))
    conn.commit()
    conn.close()

    if upload_dir:
        try:
            os.remove(os.path.join(upload_dir, filename))
        except Exception:
            pass

    return True
