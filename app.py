from flask import Flask, render_template, request, redirect, url_for, session
import joblib
import pandas as pd
import time
import os

import os
import pandas as pd
from io import BytesIO

from flask import send_file

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from flask import flash
from db import conn, cursor
from flask import send_file
import io
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph
from flask import send_file


app = Flask(__name__)
app.secret_key = "kmipps_secret_key_2026"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session["role"] != "Administrator":
            return "Access Denied. Administrator privileges required."

        return f(*args, **kwargs)

    return decorated_function

print("Current Directory:", os.getcwd())
model = joblib.load("premium_model.pkl")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        cursor.execute("""
            SELECT user_id, username, password, role
            FROM users
            WHERE username=%s;
        """, (username,))

        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):

            session["user_id"] = user[0]
            session["username"] = user[1]
            session["role"] = user[3]
            cursor.execute("""
                INSERT INTO audit_logs(
                    user_id,
                    action
            )
            VALUES(%s,%s);
            """,
            (
                user[0],
                "Logged into the system"
            ))

            conn.commit()

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    return render_template("login.html")

@app.route("/")
@login_required
def home():
    return render_template("index.html")

@app.route("/dashboard")
@login_required
def dashboard():

    # Total Drivers
    cursor.execute("SELECT COUNT(*) FROM drivers;")
    total_drivers = cursor.fetchone()[0]

    # Total Vehicles
    cursor.execute("SELECT COUNT(*) FROM vehicles;")
    total_vehicles = cursor.fetchone()[0]

    # Total Predictions
    cursor.execute("SELECT COUNT(*) FROM predictions;")
    total_predictions = cursor.fetchone()[0]

    # Average Premium
    cursor.execute("""
        SELECT ROUND(AVG(predicted_premium),2)
        FROM predictions;
    """)

    average_premium = cursor.fetchone()[0]

# Highest Premium
    cursor.execute("""
        SELECT MAX(predicted_premium)
        FROM predictions;
        """)

    highest_premium = cursor.fetchone()[0]


# Lowest Premium
    cursor.execute("""
        SELECT MIN(predicted_premium)
        FROM predictions;
        """)

    lowest_premium = cursor.fetchone()[0]


# Low Risk Count
    cursor.execute("""
        SELECT COUNT(*)
        FROM predictions
        WHERE risk_category='Low Risk';
        """)

    low_risk = cursor.fetchone()[0]


# Medium Risk Count
    cursor.execute("""
        SELECT COUNT(*)
        FROM predictions
        WHERE risk_category='Medium Risk';
        """)

    medium_risk = cursor.fetchone()[0]


# High Risk Count
    cursor.execute("""
        SELECT COUNT(*)
        FROM predictions
        WHERE risk_category='High Risk';
        """)

    high_risk = cursor.fetchone()[0]

    # Recent Predictions
    cursor.execute("""
        SELECT
            d.full_name,
            v.vehicle_make,
            v.vehicle_model,
            p.predicted_premium,
            p.risk_category,
            p.created_at
        FROM predictions p
        JOIN drivers d
        ON p.driver_id = d.driver_id
        JOIN vehicles v
        ON p.vehicle_id = v.vehicle_id
        ORDER BY p.created_at DESC
        LIMIT 10;
        """)

    recent_predictions = cursor.fetchall()

# Premium by County

    cursor.execute("""
        SELECT
            county,
            ROUND(AVG(predicted_premium),2)
        FROM drivers d
        JOIN predictions p
        ON d.driver_id=p.driver_id
        GROUP BY county
        ORDER BY county;
        """)

    county_data = cursor.fetchall()

    county_names = [row[0] for row in county_data]
    county_premiums = [float(row[1]) for row in county_data]

    # Monthly Prediction Trend

    cursor.execute("""
    SELECT
        DATE_TRUNC('month', created_at)::date AS month,
        COUNT(*)
    FROM predictions
    GROUP BY DATE_TRUNC('month', created_at)
    ORDER BY DATE_TRUNC('month', created_at);
    """)

    monthly_data = cursor.fetchall()

    months = [row[0].strftime("%b %Y") for row in monthly_data]
    monthly_predictions = [row[1] for row in monthly_data]

    print("Monthly Data:", monthly_data)
    print("Months:", months)
    print("Predictions:", monthly_predictions)

    # VEHICLE TYPE DISTRIBUTION
    cursor.execute("""
        SELECT vehicle_type, COUNT(*)
        FROM vehicles
        GROUP BY vehicle_type
        ORDER BY vehicle_type;
        """)

    vehicle_data = cursor.fetchall()

    vehicle_types = [row[0] for row in vehicle_data]
    vehicle_counts = [row[1] for row in vehicle_data]

    # POLICY TYPE DISTRIBUTION
    cursor.execute("""
    SELECT
        policy_type,
        COUNT(*)
    FROM predictions
    GROUP BY policy_type
    ORDER BY policy_type;
    """)

    policy_data = cursor.fetchall()

    policy_types = [row[0] for row in policy_data]
    policy_counts = [row[1] for row in policy_data]

    # AVERAGE PREMIUM BY VEHICLE TYPE
    cursor.execute("""
        SELECT
            v.vehicle_type,
            ROUND(AVG(p.predicted_premium),2)
        FROM vehicles v
        JOIN predictions p
        ON v.vehicle_id=p.vehicle_id
        GROUP BY v.vehicle_type
        ORDER BY v.vehicle_type;
        """)

    vehicle_premium_data = cursor.fetchall()

    vehicle_type_names = [row[0] for row in vehicle_premium_data]
    vehicle_avg_premium = [float(row[1]) for row in vehicle_premium_data]

    # TOP 10 HIGHEST PREMIUMS
    cursor.execute("""
        SELECT
            d.full_name,
            p.predicted_premium
        FROM predictions p
        JOIN drivers d
        ON p.driver_id=d.driver_id
        ORDER BY predicted_premium DESC
        LIMIT 10;
        """)

    top_premium_data = cursor.fetchall()

    top_names = [row[0] for row in top_premium_data]
    top_premiums = [float(row[1]) for row in top_premium_data]

    # PREDICTION GROWTH
    cursor.execute("""
        SELECT
            DATE(created_at),
            COUNT(*)
        FROM predictions
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at);
        """)

    growth_data = cursor.fetchall()

    growth_dates = [str(row[0]) for row in growth_data]
    growth_counts = [row[1] for row in growth_data]

    print("County:", county_names)
    print("County Premium:", county_premiums)

    print("Months:", months)
    print("Monthly:", monthly_predictions)

    print("Vehicle Types:", vehicle_types)
    print("Vehicle Counts:", vehicle_counts)

    print("Policy Types:", policy_types)
    print("Policy Counts:", policy_counts)

    print("Vehicle Premium:", vehicle_type_names)
    print("Vehicle Avg:", vehicle_avg_premium)

    print("Top Names:", top_names)
    print("Top Premium:", top_premiums)

    print("Growth Dates:", growth_dates)
    print("Growth Counts:", growth_counts)    

    # Total Users
    cursor.execute("""
        SELECT COUNT(*)
        FROM users;
    """)
    total_users = cursor.fetchone()[0]

    # Total Audit Logs
    cursor.execute("""
        SELECT COUNT(*)
        FROM audit_logs;
    """)
    total_logs = cursor.fetchone()[0]

    # Total Administrators
    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE role='Administrator';
    """)
    total_admins = cursor.fetchone()[0]

    # Total Underwriters
    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE role='Underwriter';
    """)
    total_underwriters = cursor.fetchone()[0]
    return render_template(
        "dashboard.html",
        total_drivers=total_drivers,
        total_vehicles=total_vehicles,
        total_predictions=total_predictions,
        average_premium=average_premium,
        highest_premium=highest_premium,
        lowest_premium=lowest_premium,
        low_risk=low_risk,
        medium_risk=medium_risk,
        high_risk=high_risk,
        recent_predictions=recent_predictions,
        county_names=county_names,
        county_premiums=county_premiums,
        months=months,
        monthly_predictions=monthly_predictions,
        vehicle_types=vehicle_types,
        vehicle_counts=vehicle_counts,
        policy_types=policy_types,
        policy_counts=policy_counts,
        vehicle_type_names=vehicle_type_names,
        vehicle_avg_premium=vehicle_avg_premium,
        top_names=top_names,
        top_premiums=top_premiums,
        growth_dates=growth_dates,
        growth_counts=growth_counts,
        total_users=total_users,
        total_logs=total_logs,
        total_admins=total_admins,
        total_underwriters=total_underwriters
    )

@app.route("/reports")
@login_required
def reports():

    return render_template("reports.html")

@app.route("/model-performance")
@login_required
def model_performance():

    models = [

        {
            "name": "Linear Regression",
            "mae": 592.373,
            "rmse": 742.590,
            "r2": 0.999695
        },

        {
            "name": "Random Forest",
            "mae": 1406.829,
            "rmse": 1797.730,
            "r2": 0.998214
        },

        {
            "name": "Gradient Boosting",
            "mae": 884.847,
            "rmse": 1136.199,
            "r2": 0.999287
        }

    ]

    return render_template(
        "model_performance.html",
        models=models
    )

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

    # Only administrators
    if session["role"] != "Administrator":
        return "Access Denied"

    if request.method == "POST":

        company_name = request.form["company_name"]
        company_email = request.form["company_email"]
        company_phone = request.form["company_phone"]
        company_address = request.form["company_address"]
        default_currency = request.form["default_currency"]
        low_risk_limit = request.form["low_risk_limit"]
        medium_risk_limit = request.form["medium_risk_limit"]

        cursor.execute("""
            UPDATE settings
            SET
                company_name=%s,
                company_email=%s,
                company_phone=%s,
                company_address=%s,
                default_currency=%s,
                low_risk_limit=%s,
                medium_risk_limit=%s
            WHERE setting_id=1;
        """,
        (
            company_name,
            company_email,
            company_phone,
            company_address,
            default_currency,
            low_risk_limit,
            medium_risk_limit
        ))

        conn.commit()

        cursor.execute("""
            INSERT INTO audit_logs(
                user_id,
                action
            )
            VALUES(%s,%s);
        """,
        (
            session["user_id"],
            "Updated system settings"
        ))

        conn.commit()

        flash("Settings updated successfully.", "success")

        return redirect(url_for("settings"))

    cursor.execute("""
        SELECT
            company_name,
            company_email,
            company_phone,
            company_address,
            default_currency,
            low_risk_limit,
            medium_risk_limit
        FROM settings
        WHERE setting_id=1;
    """)

    settings = cursor.fetchone()

    return render_template(
        "settings.html",
        settings=settings
    )

@app.route("/download_predictions_pdf")
@login_required
def download_predictions_pdf():

    cursor.execute("""
        SELECT
            d.full_name,
            v.vehicle_make,
            v.vehicle_model,
            p.predicted_premium,
            p.risk_category,
            p.created_at
        FROM predictions p
        JOIN drivers d
            ON p.driver_id=d.driver_id
        JOIN vehicles v
            ON p.vehicle_id=v.vehicle_id
        ORDER BY p.created_at DESC;
    """)

    rows = cursor.fetchall()

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "Kenya Motor Insurance Premium Prediction System (KMIPPS)",
            styles["Heading1"]
        )
    )

    elements.append(
        Paragraph(
            "Prediction Report",
            styles["Heading2"]
        )
    )

    data = [[
        "Driver",
        "Vehicle",
        "Premium",
        "Risk",
        "Date"
    ]]

    for row in rows:

        data.append([

            row[0],
            f"{row[1]} {row[2]}",
            f"KES {round(row[3],2)}",
            row[4],
            str(row[5])[:10]

        ])

    table = Table(data)

    table.setStyle(TableStyle([

        ("BACKGROUND",(0,0),(-1,0),colors.darkblue),

        ("TEXTCOLOR",(0,0),(-1,0),colors.white),

        ("GRID",(0,0),(-1,-1),1,colors.grey),

        ("BACKGROUND",(0,1),(-1,-1),colors.beige),

        ("ALIGN",(0,0),(-1,-1),"CENTER"),

        ("BOTTOMPADDING",(0,0),(-1,0),10)

    ]))

    elements.append(table)

    doc.build(elements)

    buffer.seek(0)

    return send_file(

        buffer,

        as_attachment=True,

        download_name="Prediction_Report.pdf",

        mimetype="application/pdf"

    )

@app.route("/download_predictions_excel")
@login_required
def download_predictions_excel():

    query = """
        SELECT
            d.full_name,
            d.county,
            v.vehicle_make,
            v.vehicle_model,
            v.vehicle_type,
            p.predicted_premium,
            p.risk_category,
            p.created_at
        FROM predictions p
        JOIN drivers d
            ON p.driver_id=d.driver_id
        JOIN vehicles v
            ON p.vehicle_id=v.vehicle_id
        ORDER BY p.created_at DESC;
    """

    df = pd.read_sql(query, conn)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        df.to_excel(

            writer,

            sheet_name="Predictions",

            index=False

        )

    output.seek(0)

    return send_file(

        output,

        as_attachment=True,

        download_name="Predictions.xlsx",

        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )

@app.route("/download_drivers_excel")
@login_required
def download_drivers_excel():

    query = "SELECT * FROM drivers ORDER BY driver_id;"

    df = pd.read_sql(query, conn)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        df.to_excel(

            writer,

            sheet_name="Drivers",

            index=False

        )

    output.seek(0)

    return send_file(

        output,

        as_attachment=True,

        download_name="Drivers.xlsx",

        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )

@app.route("/download_vehicles_excel")
@login_required
def download_vehicles_excel():

    query = "SELECT * FROM vehicles ORDER BY vehicle_id;"

    df = pd.read_sql(query, conn)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        df.to_excel(

            writer,

            sheet_name="Vehicles",

            index=False

        )

    output.seek(0)

    return send_file(

        output,

        as_attachment=True,

        download_name="Vehicles.xlsx",

        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )

@app.route("/download_audit_logs_excel")
@login_required
def download_audit_logs_excel():

    query = """
        SELECT *
        FROM audit_logs
        ORDER BY log_id DESC;
    """

    df = pd.read_sql(query, conn)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        df.to_excel(

            writer,

            sheet_name="Audit Logs",

            index=False

        )

    output.seek(0)

    return send_file(

        output,

        as_attachment=True,

        download_name="Audit_Logs.xlsx",

        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )

@app.route("/history")
@login_required
def history():
    
    search = request.args.get("search", "")

    if search:

        cursor.execute("""
        SELECT
            p.prediction_id,
            d.full_name,
            v.vehicle_make,
            v.vehicle_model,
            p.predicted_premium,
            p.risk_category,
            p.created_at
        FROM predictions p
        JOIN drivers d
            ON p.driver_id = d.driver_id
        JOIN vehicles v
            ON p.vehicle_id = v.vehicle_id
        WHERE
            LOWER(d.full_name) LIKE LOWER(%s)
            OR LOWER(v.vehicle_make) LIKE LOWER(%s)
            OR LOWER(v.vehicle_model) LIKE LOWER(%s)
        ORDER BY p.created_at DESC;
        """,
        (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ))

    else:

        cursor.execute("""
        SELECT
            p.prediction_id,
            d.full_name,
            v.vehicle_make,
            v.vehicle_model,
            p.predicted_premium,
            p.risk_category,
            p.created_at
        FROM predictions p
        JOIN drivers d
            ON p.driver_id = d.driver_id
        JOIN vehicles v
            ON p.vehicle_id = v.vehicle_id
        ORDER BY p.created_at DESC;
        """)

    predictions = cursor.fetchall()

    return render_template(
        "history.html",
        predictions=predictions,
        search=search
    )

@app.route("/prediction/<int:prediction_id>")
@login_required
def prediction_details(prediction_id):

    cursor.execute("""
        SELECT

            d.full_name,
            d.gender,
            d.driver_age,
            d.driving_experience,
            d.county,
            d.previous_claims,
            d.claim_amount_history,
            d.no_claim_bonus,
            d.driver_risk_score,

            v.vehicle_make,
            v.vehicle_model,
            v.vehicle_type,
            v.vehicle_age,
            v.engine_capacity,
            v.vehicle_value,
            v.annual_mileage,
            v.accident_risk_index,
            v.theft_risk_index,

            p.predicted_premium,
            p.risk_category,
            p.created_at

        FROM predictions p

        JOIN drivers d
        ON p.driver_id=d.driver_id

        JOIN vehicles v
        ON p.vehicle_id=v.vehicle_id

        WHERE p.prediction_id=%s;

    """,(prediction_id,))

    prediction = cursor.fetchone()

    return render_template(
    "prediction_details.html",
    prediction=prediction,
    prediction_id=prediction_id
)

@app.route("/prediction/<int:prediction_id>/pdf")
@login_required
def prediction_pdf(prediction_id):
    cursor.execute("""
        SELECT

            d.full_name,
            d.gender,
            d.driver_age,
            d.driving_experience,
            d.county,
            d.previous_claims,
            d.claim_amount_history,
            d.no_claim_bonus,
            d.driver_risk_score,

            v.vehicle_make,
            v.vehicle_model,
            v.vehicle_type,
            v.vehicle_age,
            v.engine_capacity,
            v.vehicle_value,
            v.annual_mileage,
            v.accident_risk_index,
            v.theft_risk_index,

            p.predicted_premium,
            p.risk_category,
            p.created_at

        FROM predictions p

        JOIN drivers d
            ON p.driver_id = d.driver_id

        JOIN vehicles v
            ON p.vehicle_id = v.vehicle_id

        WHERE p.prediction_id = %s;

    """, (prediction_id,))

    prediction = cursor.fetchone()

    if not prediction:
        return "Prediction not found."

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "<b><font size=18>KENYA MOTOR INSURANCE PREMIUM PREDICTION SYSTEM (KMIPPS)</font></b>",
            styles["Title"]
        )
    )

    elements.append(Paragraph("<br/>", styles["Normal"]))

    # Driver Information
    elements.append(
        Paragraph("<b>Driver Information</b>", styles["Heading2"])
    )

    driver_table = Table([
        ["Full Name", prediction[0]],
        ["Gender", prediction[1]],
        ["Age", str(prediction[2])],
        ["Driving Experience", f"{prediction[3]} Years"],
        ["County", prediction[4]],
        ["Previous Claims", str(prediction[5])],
        ["Claim Amount History", f"KES {prediction[6]}"],
        ["No Claim Bonus", str(prediction[7])],
        ["Driver Risk Score", str(prediction[8])]
    ])

    driver_table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("BACKGROUND",(0,0),(0,-1),colors.lightgrey),
        ("BOTTOMPADDING",(0,0),(-1,-1),8),
    ]))

    elements.append(driver_table)

    elements.append(Paragraph("<br/>", styles["Normal"]))

    # Vehicle Information
    elements.append(
        Paragraph("<b>Vehicle Information</b>", styles["Heading2"])
    )

    vehicle_table = Table([
        ["Make", prediction[9]],
        ["Model", prediction[10]],
        ["Vehicle Type", prediction[11]],
        ["Vehicle Age", f"{prediction[12]} Years"],
        ["Engine Capacity", f"{prediction[13]} cc"],
        ["Vehicle Value", f"KES {prediction[14]}"],
        ["Annual Mileage", str(prediction[15])],
        ["Accident Risk Index", str(prediction[16])],
        ["Theft Risk Index", str(prediction[17])]
    ])

    vehicle_table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("BACKGROUND",(0,0),(0,-1),colors.lightgrey),
        ("BOTTOMPADDING",(0,0),(-1,-1),8),
    ]))

    elements.append(vehicle_table)

    elements.append(Paragraph("<br/>", styles["Normal"]))

    # Prediction Result
    elements.append(
        Paragraph("<b>Prediction Result</b>", styles["Heading2"])
    )

    prediction_table = Table([
        ["Predicted Premium", f"KES {round(prediction[18],2)}"],
        ["Risk Category", prediction[19]],
        ["Date Generated", str(prediction[20])]
    ])

    prediction_table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("BACKGROUND",(0,0),(0,-1),colors.lightgrey),
        ("BOTTOMPADDING",(0,0),(-1,-1),8),
    ]))

    elements.append(prediction_table)

    elements.append(Paragraph("<br/><br/>", styles["Normal"]))

    elements.append(
        Paragraph(
            "Generated by KMIPPS",
            styles["Italic"]
        )
    )

    doc.build(elements)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Prediction_{prediction_id}.pdf",
        mimetype="application/pdf"
    )

@app.route("/audit_logs")
@login_required
def audit_logs():

    if session["role"] != "Administrator":
        return "Access Denied"

    search = request.args.get("search", "")

    if search:

        cursor.execute("""
            SELECT
                a.log_id,
                u.username,
                a.action,
                a.created_at
            FROM audit_logs a
            JOIN users u
                ON a.user_id = u.user_id
            WHERE
                LOWER(u.username) LIKE LOWER(%s)
                OR LOWER(a.action) LIKE LOWER(%s)
            ORDER BY a.created_at DESC;
        """,
        (
            f"%{search}%",
            f"%{search}%"
        ))

    else:

        cursor.execute("""
            SELECT
                a.log_id,
                u.username,
                a.action,
                a.created_at
            FROM audit_logs a
            JOIN users u
                ON a.user_id = u.user_id
            ORDER BY a.created_at DESC;
        """)

    logs = cursor.fetchall()

    return render_template(
        "audit_logs.html",
        logs=logs,
        search=search
    )

@app.route("/audit_logs/pdf")
@login_required
def audit_logs_pdf():

    if session["role"] != "Administrator":
        return "Access Denied"

    cursor.execute("""
        SELECT
            a.log_id,
            u.username,
            a.action,
            a.created_at
        FROM audit_logs a
        JOIN users u
            ON a.user_id = u.user_id
        ORDER BY a.created_at DESC;
    """)

    logs = cursor.fetchall()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()
    elements = []

    elements.append(
        Paragraph("<b>KMIPPS Audit Log Report</b>", styles["Title"])
    )

    elements.append(Paragraph("<br/>", styles["Normal"]))

    data = [["ID", "Username", "Action", "Date"]]

    for row in logs:
        data.append([
            row[0],
            row[1],
            row[2],
            str(row[3])
        ])

    table = Table(data)

    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("BACKGROUND",(0,1),(-1,-1),colors.beige),
        ("BOTTOMPADDING",(0,0),(-1,0),8),
    ]))

    elements.append(table)

    doc.build(elements)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Audit_Logs.pdf",
        mimetype="application/pdf"
    )

@app.route("/audit_logs/excel")
@login_required
def audit_logs_excel():

    if session["role"] != "Administrator":
        return "Access Denied"

    cursor.execute("""
        SELECT
            a.log_id,
            u.username,
            a.action,
            a.created_at
        FROM audit_logs a
        JOIN users u
            ON a.user_id = u.user_id
        ORDER BY a.created_at DESC;
    """)

    logs = cursor.fetchall()

    df = pd.DataFrame(
        logs,
        columns=[
            "Log ID",
            "Username",
            "Action",
            "Created At"
        ]
    )

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Audit Logs"
        )

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="Audit_Logs.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
  
@app.route("/export_excel")
@login_required
def export_excel():

    cursor.execute("""
        SELECT
            d.full_name,
            v.vehicle_make,
            v.vehicle_model,
            p.predicted_premium,
            p.risk_category,
            p.created_at
        FROM predictions p
        JOIN drivers d
            ON p.driver_id = d.driver_id
        JOIN vehicles v
            ON p.vehicle_id = v.vehicle_id
        ORDER BY p.created_at DESC;
    """)

    rows = cursor.fetchall()

    df = pd.DataFrame(rows, columns=[
        "Full Name",
        "Vehicle Make",
        "Vehicle Model",
        "Premium (KES)",
        "Risk Category",
        "Prediction Date"
    ])

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Predictions")

    output.seek(0)

    return send_file(
        output,
        download_name="KMIPPS_Predictions.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route("/export_pdf")
@login_required
def export_pdf():

    cursor.execute("""
        SELECT
            d.full_name,
            v.vehicle_make,
            v.vehicle_model,
            p.predicted_premium,
            p.risk_category,
            p.created_at
        FROM predictions p
        JOIN drivers d
            ON p.driver_id = d.driver_id
        JOIN vehicles v
            ON p.vehicle_id = v.vehicle_id
        ORDER BY p.created_at DESC;
    """)

    rows = cursor.fetchall()

    output = io.BytesIO()

    doc = SimpleDocTemplate(output)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "<b>Kenya Motor Insurance Premium Prediction System</b>",
            styles["Title"]
        )
    )

    elements.append(
        Paragraph(
            "Prediction History Report",
            styles["Heading2"]
        )
    )

    table_data = [[
        "Name",
        "Make",
        "Model",
        "Premium",
        "Risk",
        "Date"
    ]]

    for row in rows:

        table_data.append([
            row[0],
            row[1],
            row[2],
            f"KES {row[3]:,.2f}",
            row[4],
            str(row[5])
        ])

    table = Table(table_data)

    table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("GRID", (0,0), (-1,-1), 1, colors.black),

        ("BACKGROUND", (0,1), (-1,-1), colors.beige),

        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),

        ("ALIGN", (0,0), (-1,-1), "CENTER"),

        ("BOTTOMPADDING", (0,0), (-1,0), 12)

    ]))

    elements.append(table)

    doc.build(elements)

    output.seek(0)

    return send_file(
        output,
        download_name="KMIPPS_Report.pdf",
        as_attachment=True,
        mimetype="application/pdf"
    )

@app.route("/users")
@admin_required
def users():

    cursor.execute("""
        SELECT
            user_id,
            username,
            password,
            role
        FROM users
        ORDER BY username;
    """)

    users = cursor.fetchall()

    return render_template(
        "users.html",
        users=users
    )

@app.route("/add_user", methods=["GET","POST"])
@admin_required
def add_user():

    if request.method == "POST":

        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        role = request.form["role"]

        cursor.execute("""
            INSERT INTO users
            (username, password, role)
            VALUES (%s, %s, %s);
        """, (username, password, role))

        conn.commit()

        cursor.execute("""
        INSERT INTO audit_logs(
            user_id,
            action
        )
        VALUES(%s,%s);
        """,
        (
            session["user_id"],
            f"Created user {username}"
        ))

        conn.commit()

        flash("User created successfully.", "success")

        return redirect(url_for("users"))
    return render_template("add_user.html")

@app.route("/edit_user/<int:user_id>", methods=["GET","POST"])
@admin_required
def edit_user(user_id):

    if request.method == "POST":

        username = request.form["username"]
        role = request.form["role"]

        cursor.execute("""
            UPDATE users
            SET username=%s,
                role=%s
            WHERE user_id=%s;
        """, (username, role, user_id))

        conn.commit()

        cursor.execute("""
            INSERT INTO audit_logs(
                user_id,
                action
        )
        VALUES(%s,%s);
        """,
        (
            session["user_id"],
            f"Updated user {username}"
        ))

        conn.commit()

        flash("User updated successfully.", "success")

        return redirect(url_for("users"))

@app.route("/delete_user/<int:user_id>")
@admin_required
def delete_user(user_id):

    # Prevent admin from deleting themselves
    if session["user_id"] == user_id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("users"))

    # Get the username before deleting
    cursor.execute("""
        SELECT username
        FROM users
        WHERE user_id=%s;
    """, (user_id,))

    user = cursor.fetchone()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("users"))

    username = user[0]

    # Delete the user
    cursor.execute("""
        DELETE FROM users
        WHERE user_id=%s;
    """, (user_id,))

    conn.commit()

    # Record the action in the audit log
    cursor.execute("""
        INSERT INTO audit_logs (
            user_id,
            action
        )
        VALUES (%s, %s);
    """,
    (
        session["user_id"],
        f"Deleted user {username}"
    ))

    conn.commit()

    flash("User deleted successfully.", "success")

    return redirect(url_for("users"))

@app.route("/predict", methods=["POST"])
@login_required
def predict():
    full_name = request.form["full_name"]

    data = {
        "driver_age": int(request.form["driver_age"]),
        "gender": request.form["gender"],
        "driving_experience": int(request.form["driving_experience"]),
        "vehicle_make": request.form["vehicle_make"],
        "vehicle_model": request.form["vehicle_model"],
        "vehicle_type": request.form["vehicle_type"],
        "vehicle_age": int(request.form["vehicle_age"]),
        "engine_capacity": int(request.form["engine_capacity"]),
        "vehicle_value": float(request.form["vehicle_value"]),
        "county": request.form["county"],
        "annual_mileage": int(request.form["annual_mileage"]),
        "previous_claims": int(request.form["previous_claims"]),
        "claim_amount_history": float(request.form["claim_amount_history"]),
        "no_claim_bonus": int(request.form["no_claim_bonus"]),
        "policy_type": request.form["policy_type"],
        "accident_risk_index": float(request.form["accident_risk_index"]),
        "theft_risk_index": float(request.form["theft_risk_index"]),
        "driver_risk_score": float(request.form["driver_risk_score"])
    }

    start = time.time()

    prediction = model.predict(
        pd.DataFrame([data])
    )[0]

    processing_time = round(time.time() - start, 3)
    # Get risk limits from Settings table

    cursor.execute("""
        SELECT
            low_risk_limit,
            medium_risk_limit
        FROM settings
        WHERE setting_id = 1;
    """)

    limits = cursor.fetchone()

    low_limit = limits[0]
    medium_limit = limits[1]

    risk_score = data["driver_risk_score"]

    if risk_score < low_limit:
        risk_category = "Low Risk"

    elif risk_score < medium_limit:
        risk_category = "Medium Risk"

    else:
        risk_category = "High Risk"

    cursor.execute("""
    INSERT INTO drivers(
        full_name,
        gender,
        driver_age,
        driving_experience,
        county,
        previous_claims,
        claim_amount_history,
        no_claim_bonus,
        driver_risk_score
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    RETURNING driver_id;
    """,
    (
        full_name,
        data["gender"],
        data["driver_age"],
        data["driving_experience"],
        data["county"],
        data["previous_claims"],
        data["claim_amount_history"],
        data["no_claim_bonus"],
        data["driver_risk_score"]
    ))

    driver_id = cursor.fetchone()[0]

    conn.commit()

    cursor.execute("""
INSERT INTO vehicles(
    vehicle_make,
    vehicle_model,
    vehicle_type,
    vehicle_age,
    engine_capacity,
    vehicle_value,
    annual_mileage,
    accident_risk_index,
    theft_risk_index
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    RETURNING vehicle_id;
    """,
    (
        data["vehicle_make"],
        data["vehicle_model"],
        data["vehicle_type"],
        data["vehicle_age"],
        data["engine_capacity"],
        data["vehicle_value"],
        data["annual_mileage"],
        data["accident_risk_index"],
        data["theft_risk_index"]
    ))

    vehicle_id = cursor.fetchone()[0]

    conn.commit()

    cursor.execute("""
    INSERT INTO predictions(

        driver_id,
        vehicle_id,
        predicted_premium,
        risk_category,
        policy_type,
        insurer,
        broker,
        prediction_model,
        processing_time

    )

    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s);

    """,
    (

        driver_id,
        vehicle_id,
        float(prediction),
        risk_category,

        data["policy_type"],

        "KMIPPS Insurance",

        "Diaspora Insurance Agency",

        "Gradient Boosting",

        processing_time

    ))
    conn.commit()

    cursor.execute("""
    INSERT INTO audit_logs(
        user_id,
        action
    )
    VALUES(%s,%s);
    """,
    (
        session["user_id"],
        f"Created prediction for {full_name}"
    ))

    conn.commit()
    return render_template(
        "result.html",
        premium=round(prediction, 2),
        risk_category=risk_category
    )

@app.route("/logout")
@login_required
def logout():

    cursor.execute("""
    INSERT INTO audit_logs(
        user_id,
        action
    )
    VALUES(%s,%s);
    """,
    (
        session["user_id"],
        "Logged out"
    ))

    conn.commit()

    session.clear()

    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)