from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from pyzbar.pyzbar import decode
from PIL import Image
import sqlite3
import qrcode
import os
import uuid

app = Flask(__name__)
app.secret_key = "mysecretkey123"

QR_FOLDER = "static/qr_codes"
LOGO_FOLDER = "static/logos"

os.makedirs(QR_FOLDER, exist_ok=True)
os.makedirs(LOGO_FOLDER, exist_ok=True)


# ======================
# REGISTER
# ======================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = generate_password_hash(
            request.form["password"]
        )

        conn = sqlite3.connect("qr.db")
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO users(username, password)
                VALUES (?, ?)
                """,
                (username, password)
            )

            conn.commit()

            return redirect("/login")

        except sqlite3.IntegrityError:

            return "Username already exists"

        finally:

            conn.close()

    return render_template("register.html")


# ======================
# LOGIN
# ======================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("qr.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username=?
            """,
            (username,)
        )

        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(
            user[2],
            password
        ):

            session["user"] = user[1]
            session["user_id"] = user[0]

            return redirect("/")

        return "Invalid Username or Password"

    return render_template("login.html")


# ======================
# LOGOUT
# ======================

@app.route("/logout")
def logout():

    session.pop("user", None)
    session.pop("user_id", None)

    return redirect("/login")


# ======================
# HOME
# ======================

@app.route("/", methods=["GET", "POST"])
def home():

    if "user" not in session:
        return redirect("/login")

    qr_image = None

    if request.method == "POST":

        data = request.form["data"]
        qr_type = request.form["qr_type"]
        qr_color = request.form["qr_color"]

        # QR Templates

        if qr_type == "website":

            if not data.startswith("http"):
                data = "https://" + data

        elif qr_type == "whatsapp":

            data = f"https://wa.me/{data}"

        elif qr_type == "wifi":

            data = f"WIFI:T:WPA;S:{data};P:password;;"

        # Create QR

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )

        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(
            fill_color=qr_color,
            back_color="white"
        ).convert("RGB")

        # Logo Upload

        logo_file = request.files.get("logo")

        if logo_file and logo_file.filename:

            logo_path = os.path.join(
                LOGO_FOLDER,
                logo_file.filename
            )

            logo_file.save(logo_path)

            logo = Image.open(logo_path)

            qr_width, qr_height = img.size

            logo_size = qr_width // 4

            logo = logo.resize(
                (logo_size, logo_size)
            )

            position = (
                (qr_width - logo_size) // 2,
                (qr_height - logo_size) // 2
            )

            if logo.mode == "RGBA":

                img.paste(
                    logo,
                    position,
                    logo
                )

            else:

                img.paste(
                    logo,
                    position
                )

        filename = f"{uuid.uuid4()}.png"

        filepath = os.path.join(
            QR_FOLDER,
            filename
        )

        img.save(filepath)

        conn = sqlite3.connect("qr.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO qr_history
            (text, image, user_id, created_at)
            VALUES (?, ?, ?, datetime('now'))
            """,
            (
                data,
                filename,
                session["user_id"]
            )
        )

        conn.commit()
        conn.close()

        qr_image = "/" + filepath.replace("\\", "/")

    return render_template(
        "index.html",
        qr_image=qr_image,
        username=session["user"]
    )

@app.route("/scan", methods=["GET", "POST"])
def scan():

    if "user" not in session:
        return redirect("/login")

    result = None

    if request.method == "POST":

        file = request.files["qr_file"]

        if file:

            path = os.path.join(
                "static",
                file.filename
            )

            file.save(path)

            img = Image.open(path)

            decoded = decode(img)

            if decoded:

                result = decoded[0].data.decode("utf-8")

    return render_template(
        "scan.html",
        result=result
    )

@app.route("/export_pdf")
def export_pdf():

    if "user" not in session:
        return redirect("/login")

    pdf_path = "static/report.pdf"

    doc = SimpleDocTemplate(pdf_path)

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph(
            "QR Generator Report",
            styles["Title"]
        )
    )

    content.append(Spacer(1, 20))

    conn = sqlite3.connect("qr.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT text, created_at
    FROM qr_history
    WHERE user_id=?
    ORDER BY id DESC
    """,
    (session["user_id"],))

    rows = cursor.fetchall()

    conn.close()

    for row in rows:

        content.append(
            Paragraph(
                f"Text: {row[0]}",
                styles["BodyText"]
            )
        )

        content.append(
            Paragraph(
                f"Date: {row[1]}",
                styles["BodyText"]
            )
        )

        content.append(
            Spacer(1, 10)
        )

    doc.build(content)

    return redirect("/static/report.pdf")

# ======================
# HISTORY
# ======================

@app.route("/history")
def history():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("qr.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM qr_history
        WHERE user_id=?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    )

    records = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        records=records
    )


# ======================
# DELETE
# ======================

@app.route("/delete/<int:id>")
def delete(id):

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("qr.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM qr_history
        WHERE id=? AND user_id=?
        """,
        (
            id,
            session["user_id"]
        )
    )

    conn.commit()
    conn.close()

    return redirect("/history")


# ======================
# DASHBOARD
# ======================

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("qr.db")
    cursor = conn.cursor()

    # Total QR Codes

    cursor.execute("""
    SELECT COUNT(*)
    FROM qr_history
    WHERE user_id=?
    """,
    (session["user_id"],))

    total_qr = cursor.fetchone()[0]

    # Latest 5 QR Codes

    cursor.execute("""
    SELECT *
    FROM qr_history
    WHERE user_id=?
    ORDER BY id DESC
    LIMIT 5
    """,
    (session["user_id"],))

    recent_qr = cursor.fetchall()

    recent_count = len(recent_qr)

    # Chart Analytics Data

    cursor.execute("""
    SELECT DATE(created_at), COUNT(*)
    FROM qr_history
    WHERE user_id=?
    GROUP BY DATE(created_at)
    ORDER BY DATE(created_at)
    """,
    (session["user_id"],))

    chart_data = cursor.fetchall()

    labels = [row[0] for row in chart_data]
    values = [row[1] for row in chart_data]

    for row in chart_data:
        labels.append(row[0])
        values.append(row[1])

    conn.close()

    return render_template(
        "dashboard.html",
        username=session["user"],
        total_qr=total_qr,
        recent_count=recent_count,
        recent_qr=recent_qr,
        labels=labels,
        values=values
    )


@app.route("/admin")
def admin():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("qr.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM qr_history")
    total_qrs = cursor.fetchone()[0]

    cursor.execute("""
        SELECT username
        FROM users
        ORDER BY id DESC
        LIMIT 5
    """)

    latest_users = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        total_users=total_users,
        total_qrs=total_qrs,
        latest_users=latest_users
    )

@app.route("/admin/users")
def admin_users():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("qr.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username
        FROM users
        ORDER BY id DESC
    """)

    users = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_users.html",
        users=users
    )

# ======================
# MAIN
# ======================

if __name__ == "__main__":
    app.run(debug=True)