
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session
)

from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)

from werkzeug.security import (
    generate_password_hash, check_password_hash
)

import mysql.connector
import os
import secrets
import time


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "CHANGE_THIS_SECRET_KEY_BEFORE_RUNNING"
)


# =========================================================
# MYSQL CONFIGURATION
# =========================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Root@123",
    "database": "ai_smart_toll"
}


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


# =========================================================
# OTP AND PASSWORD SETTINGS
# =========================================================

OTP_EXPIRY_SECONDS = 300
MAX_OTP_ATTEMPTS = 5


def password_meets_policy(password):
    return (
        len(password) >= 8
        and any(char.isupper() for char in password)
        and any(char.islower() for char in password)
        and any(char.isdigit() for char in password)
        and any(not char.isalnum() for char in password)
    )


def password_policy_message():
    return (
        "Password must be at least 8 characters and include an uppercase "
        "letter, a lowercase letter, a number, and a special character."
    )


# =========================================================
# FLASK LOGIN
# =========================================================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# =========================================================
# USER CLASS
# =========================================================

class User(UserMixin):

    def __init__(self, user_id, name, email, role="operator"):
        self.id = user_id
        self.name = name
        self.email = email
        self.role = role


# =========================================================
# LOAD USER
# =========================================================

@login_manager.user_loader
def load_user(user_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, name, email, role
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if user:
            return User(
                user["id"],
                user["name"],
                user["email"],
                user.get("role", "operator")
            )

    except mysql.connector.Error as error:
        print("Load user error:", error)

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return None


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter your email and password.", "warning")
            return render_template("login.html")

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id, name, email, password, role
                FROM users
                WHERE LOWER(email) = %s
                """,
                (email,)
            )

            user_data = cursor.fetchone()

            if user_data and check_password_hash(
                user_data["password"], password
            ):

                user = User(
                    user_data["id"],
                    user_data["name"],
                    user_data["email"],
                    user_data.get("role", "operator")
                )

                login_user(user)

                flash("Login successful.", "success")
                return redirect(url_for("dashboard"))

            flash("Invalid email or password.", "danger")

        except mysql.connector.Error as error:
            print("Login database error:", error)
            flash("Unable to connect to the database.", "danger")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template("login.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            flash("Please fill in all required fields.", "warning")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if not password_meets_policy(password):
            flash(password_policy_message(), "warning")
            return render_template("register.html")

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                "SELECT id FROM users WHERE LOWER(email) = %s",
                (email,)
            )

            if cursor.fetchone():
                flash("An account with this email already exists.", "warning")
                return render_template("register.html")

            hashed_password = generate_password_hash(password)

            cursor.execute(
                """
                INSERT INTO users (name, email, password, role)
                VALUES (%s, %s, %s, %s)
                """,
                (name, email, hashed_password, "operator")
            )

            connection.commit()

            flash("Registration successful. Please login.", "success")
            return redirect(url_for("login"))

        except mysql.connector.Error as error:
            if connection:
                connection.rollback()

            app.logger.exception("Registration database error: %s", error)
            flash("Unable to create account. Please try again.", "danger")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template("register.html")


# =========================================================
# FORGOT PASSWORD - OTP IN VS CODE TERMINAL
# =========================================================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()

        if not email:
            flash("Please enter your email address.", "warning")
            return render_template("forgot_password.html")

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE LOWER(email) = %s
                """,
                (email,)
            )

            user = cursor.fetchone()

            if not user:
                flash("No account was found with this email.", "danger")
                return render_template("forgot_password.html")

            # Generate a secure six-digit OTP
            otp = str(secrets.randbelow(900000) + 100000)

            # Clear any previous OTP verification
            session.pop("otp_verified", None)

            # Store reset information in the session
            session["reset_email"] = email

            session["reset_otp_hash"] = generate_password_hash(
                otp
            )

            session["reset_otp_expires_at"] = (
                time.time() + OTP_EXPIRY_SECONDS
            )

            session["reset_otp_attempts"] = 0

            # Display OTP in VS Code terminal
            print("\n")
            print("=" * 50)
            print("       AI TOLLGUARD - PASSWORD RECOVERY")
            print("=" * 50)
            print(f"Registered Email : {email}")
            print(f"Your OTP         : {otp}")
            print("Validity         : 5 Minutes")
            print("=" * 50)
            print("\n")

            flash(
                "Your verification code has been generated. "
                "Check the VS Code terminal.",
                "success"
            )

            return redirect(url_for("verify_otp"))

        except mysql.connector.Error as error:
            app.logger.exception(
                "Forgot password database error: %s", error
            )

            flash(
                "A database error occurred. Please try again.",
                "danger"
            )

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template("forgot_password.html")


# =========================================================
# VERIFY OTP
# =========================================================

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():

    if (
        "reset_email" not in session
        or "reset_otp_hash" not in session
    ):
        return redirect(url_for("forgot_password"))

    if request.method == "POST":

        entered_otp = request.form.get("otp", "").strip()
        stored_hash = session.get("reset_otp_hash")
        expires_at = session.get("reset_otp_expires_at", 0)
        attempts = session.get("reset_otp_attempts", 0)

        if time.time() > expires_at:

            for key in (
                "reset_email",
                "reset_otp_hash",
                "reset_otp_expires_at",
                "reset_otp_attempts",
                "otp_verified"
            ):
                session.pop(key, None)

            flash(
                "Your OTP has expired. Please request a new one.",
                "warning"
            )

            return redirect(url_for("forgot_password"))

        if attempts >= MAX_OTP_ATTEMPTS:

            for key in (
                "reset_email",
                "reset_otp_hash",
                "reset_otp_expires_at",
                "reset_otp_attempts",
                "otp_verified"
            ):
                session.pop(key, None)

            flash(
                "Too many incorrect attempts. Please request a new OTP.",
                "danger"
            )

            return redirect(url_for("forgot_password"))

        if (
            not entered_otp
            or len(entered_otp) != 6
            or not entered_otp.isdigit()
        ):
            flash("Please enter the 6-digit OTP.", "warning")
            return render_template("verify_otp.html")

        if stored_hash and check_password_hash(
            stored_hash, entered_otp
        ):

            session["otp_verified"] = True

            session.pop("reset_otp_hash", None)
            session.pop("reset_otp_expires_at", None)
            session.pop("reset_otp_attempts", None)

            return redirect(url_for("reset_password"))

        session["reset_otp_attempts"] = attempts + 1

        remaining = (
            MAX_OTP_ATTEMPTS - session["reset_otp_attempts"]
        )

        flash(
            f"Invalid OTP. {remaining} attempt(s) remaining.",
            "danger"
        )

    return render_template("verify_otp.html")


# =========================================================
# RESET PASSWORD
# =========================================================

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    if (
        not session.get("otp_verified")
        or not session.get("reset_email")
    ):
        return redirect(url_for("forgot_password"))

    if request.method == "POST":

        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not new_password or not confirm_password:
            flash("Please enter both password fields.", "warning")
            return render_template("reset_password.html")

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("reset_password.html")

        if not password_meets_policy(new_password):
            flash(password_policy_message(), "warning")
            return render_template("reset_password.html")

        email = session.get("reset_email")

        hashed_password = generate_password_hash(new_password)

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE users
                SET password = %s
                WHERE LOWER(email) = %s
                """,
                (hashed_password, email)
            )

            if cursor.rowcount != 1:
                connection.rollback()

                flash(
                    "Unable to find the account. "
                    "Please restart password reset.",
                    "danger"
                )

                return redirect(url_for("forgot_password"))

            connection.commit()

            for key in (
                "reset_email",
                "reset_otp_hash",
                "reset_otp_expires_at",
                "reset_otp_attempts",
                "otp_verified"
            ):
                session.pop(key, None)

            flash(
                "Password reset successfully. Please login.",
                "success"
            )

            return redirect(url_for("login"))

        except mysql.connector.Error as error:
            if connection:
                connection.rollback()

            app.logger.exception(
                "Reset password database error: %s", error
            )

            flash(
                "Unable to reset password. Please try again.",
                "danger"
            )

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template("reset_password.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("You have been logged out.", "success")

    return redirect(url_for("login"))


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    connection = None
    cursor = None

    total_transactions = 0
    normal_transactions = 0
    fraud_transactions = 0
    total_revenue = 0
    recent_transactions = []
    recent_notifications = []

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT COUNT(*) AS total FROM transactions"
        )
        result = cursor.fetchone()

        if result:
            total_transactions = result["total"] or 0

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM transactions
            WHERE status = 'Normal'
            """
        )
        result = cursor.fetchone()

        if result:
            normal_transactions = result["total"] or 0

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM transactions
            WHERE status = 'Fraud'
            """
        )
        result = cursor.fetchone()

        if result:
            fraud_transactions = result["total"] or 0

        cursor.execute(
            """
            SELECT COALESCE(SUM(transaction_amount), 0) AS revenue
            FROM transactions
            WHERE status = 'Normal'
            """
        )
        result = cursor.fetchone()

        if result:
            total_revenue = result["revenue"] or 0

        cursor.execute(
            """
            SELECT
                id, vehicle_number, toll_plaza,
                transaction_amount, transaction_time, status
            FROM transactions
            ORDER BY id DESC
            LIMIT 5
            """
        )
        recent_transactions = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                id, title, message, notification_type,
                is_read, created_at
            FROM notifications
            ORDER BY id DESC
            LIMIT 5
            """
        )
        recent_notifications = cursor.fetchall()

    except mysql.connector.Error as error:
        print("Dashboard error:", error)
        flash("Unable to load dashboard data.", "danger")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template(
        "dashboard.html",
        total=total_transactions,
        normal=normal_transactions,
        fraud=fraud_transactions,
        total_revenue=total_revenue,
        recent_transactions=recent_transactions,
        recent_notifications=recent_notifications
    )


# =========================================================
# ADD VEHICLE FROM TRANSACTION PAGE
# =========================================================

@app.route("/add-vehicle-from-transaction", methods=["POST"])
@login_required
def add_vehicle_from_transaction():

    vehicle_number = request.form.get(
        "vehicle_number", ""
    ).strip().upper()

    vehicle_type = request.form.get(
        "vehicle_type", ""
    ).strip()

    owner_name = request.form.get(
        "owner_name", ""
    ).strip()

    if not vehicle_number:
        flash("Please enter a vehicle number.", "warning")
        return redirect(url_for("transactions_page"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM vehicles
            WHERE vehicle_number = %s
            """,
            (vehicle_number,)
        )

        if cursor.fetchone():
            flash("This vehicle is already registered.", "warning")
            return redirect(url_for("transactions_page"))

        cursor.execute(
            """
            INSERT INTO vehicles
            (vehicle_number, vehicle_type, owner_name)
            VALUES (%s, %s, %s)
            """,
            (vehicle_number, vehicle_type, owner_name)
        )

        connection.commit()

        flash(
            f"Vehicle {vehicle_number} added successfully.",
            "success"
        )

    except mysql.connector.Error as error:
        if connection:
            connection.rollback()

        print("Add vehicle error:", error)
        flash("Unable to add vehicle.", "danger")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for("transactions_page"))


# =========================================================
# ADD TOLL PLAZA FROM TRANSACTION PAGE
# =========================================================

@app.route("/add-plaza-from-transaction", methods=["POST"])
@login_required
def add_plaza_from_transaction():

    plaza_name = request.form.get(
        "plaza_name", ""
    ).strip()

    location = request.form.get(
        "location", ""
    ).strip()

    toll_amount_text = request.form.get(
        "toll_amount", "0"
    ).strip()

    if not plaza_name:
        flash("Please enter a toll plaza name.", "warning")
        return redirect(url_for("transactions_page"))

    try:
        toll_amount = float(toll_amount_text or 0)
    except ValueError:
        flash("Please enter a valid toll amount.", "danger")
        return redirect(url_for("transactions_page"))

    if toll_amount < 0:
        flash("Toll amount cannot be negative.", "danger")
        return redirect(url_for("transactions_page"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM toll_plazas
            WHERE LOWER(plaza_name) = LOWER(%s)
            """,
            (plaza_name,)
        )

        if cursor.fetchone():
            flash("This toll plaza is already registered.", "warning")
            return redirect(url_for("transactions_page"))

        cursor.execute(
            """
            INSERT INTO toll_plazas
            (plaza_name, location, toll_amount)
            VALUES (%s, %s, %s)
            """,
            (plaza_name, location, toll_amount)
        )

        connection.commit()

        flash(
            f"Toll plaza {plaza_name} added successfully.",
            "success"
        )

    except mysql.connector.Error as error:
        if connection:
            connection.rollback()

        print("Add toll plaza error:", error)
        flash("Unable to add toll plaza.", "danger")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for("transactions_page"))


# =========================================================
# TRANSACTIONS
# =========================================================

@app.route("/transactions", methods=["GET", "POST"])
@login_required
def transactions_page():

    if request.method == "POST":

        vehicle_number = request.form.get(
            "vehicle_number", ""
        ).strip().upper()

        toll_plaza = request.form.get(
            "toll_plaza", ""
        ).strip()

        amount_text = request.form.get(
            "amount", "0"
        ).strip()

        if not vehicle_number:
            flash("Please select a vehicle.", "warning")
            return redirect(url_for("transactions_page"))

        if not toll_plaza:
            flash("Please select a toll plaza.", "warning")
            return redirect(url_for("transactions_page"))

        try:
            amount = float(amount_text or 0)
        except ValueError:
            flash("Please enter a valid amount.", "danger")
            return redirect(url_for("transactions_page"))

        if amount < 0:
            flash("Transaction amount cannot be negative.", "danger")
            return redirect(url_for("transactions_page"))

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            # Check vehicle
            cursor.execute(
                """
                SELECT id
                FROM vehicles
                WHERE vehicle_number = %s
                """,
                (vehicle_number,)
            )

            vehicle = cursor.fetchone()

            if not vehicle:
                flash("Vehicle is not registered.", "warning")
                return redirect(url_for("transactions_page"))

            # Check toll plaza
            cursor.execute(
                """
                SELECT id
                FROM toll_plazas
                WHERE LOWER(plaza_name) = LOWER(%s)
                """,
                (toll_plaza,)
            )

            plaza = cursor.fetchone()

            if not plaza:
                flash("Toll plaza is not registered.", "warning")
                return redirect(url_for("transactions_page"))

            # Check repeated transactions within 30 minutes
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM transactions
                WHERE vehicle_number = %s
                  AND LOWER(toll_plaza) = LOWER(%s)
                  AND transaction_time BETWEEN
                      DATE_SUB(NOW(), INTERVAL 30 MINUTE) AND NOW()
                """,
                (vehicle_number, toll_plaza)
            )

            recent_repeat = cursor.fetchone()

            recent_repeat_count = (
                recent_repeat["total"] if recent_repeat else 0
            )

            if recent_repeat_count > 0:
                status = "Fraud"
                fraud_score = 85.00
                fraud_reason = (
                    "Repeated vehicle transaction at the same "
                    "toll plaza within 30 minutes."
                )
            else:
                status = "Normal"
                fraud_score = 8.00
                fraud_reason = (
                    "No repeat transaction at the same toll plaza "
                    "was found within the last 30 minutes."
                )

            # Insert transaction
            cursor.execute(
                """
                INSERT INTO transactions
                (
                    vehicle_number,
                    toll_plaza,
                    transaction_amount,
                    status
                )
                VALUES (%s, %s, %s, %s)
                """,
                (vehicle_number, toll_plaza, amount, status)
            )

            transaction_id = cursor.lastrowid

            # Insert fraud record when fraud is detected
            if status == "Fraud":

                cursor.execute(
                    """
                    INSERT INTO fraud_records
                    (
                        transaction_id,
                        fraud_type,
                        fraud_score,
                        reason
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        transaction_id,
                        "Repeated Transaction",
                        fraud_score,
                        fraud_reason
                    )
                )

            # Create notification
            if status == "Fraud":

                cursor.execute(
                    """
                    INSERT INTO notifications
                    (title, message, notification_type)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        "Fraud Detected",
                        (
                            f"Suspicious transaction detected "
                            f"for vehicle {vehicle_number} "
                            f"at {toll_plaza}."
                        ),
                        "fraud"
                    )
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO notifications
                    (title, message, notification_type)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        "Transaction Recorded",
                        (
                            f"Normal transaction recorded "
                            f"for vehicle {vehicle_number}."
                        ),
                        "success"
                    )
                )

            connection.commit()

            if status == "Fraud":
                flash(
                    "Transaction recorded. Fraud detected.",
                    "danger"
                )
            else:
                flash(
                    "Transaction recorded successfully.",
                    "success"
                )

        except mysql.connector.Error as error:
            if connection:
                connection.rollback()

            print("Transaction error:", error)
            flash("Unable to save transaction.", "danger")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return redirect(url_for("transactions_page"))

    # GET TRANSACTIONS

    transaction_list = []
    vehicles = []
    toll_plazas = []

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, vehicle_number, vehicle_type, owner_name
            FROM vehicles
            ORDER BY vehicle_number
            """
        )
        vehicles = cursor.fetchall()

        cursor.execute(
            """
            SELECT id, plaza_name, location, toll_amount
            FROM toll_plazas
            ORDER BY plaza_name
            """
        )
        toll_plazas = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                id, vehicle_number, toll_plaza,
                transaction_amount, transaction_time, status
            FROM transactions
            ORDER BY id DESC
            """
        )
        transaction_list = cursor.fetchall()

    except mysql.connector.Error as error:
        print("Load transactions error:", error)
        flash("Unable to load transaction data.", "danger")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template(
        "transactions.html",
        transactions=transaction_list,
        vehicles=vehicles,
        toll_plazas=toll_plazas
    )


# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
@login_required
def reports():

    connection = None
    cursor = None

    total_transactions = 0
    normal_transactions = 0
    fraud_transactions = 0
    total_revenue = 0
    fraud_loss = 0
    report_transactions = []

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT COUNT(*) AS total FROM transactions"
        )
        result = cursor.fetchone()

        if result:
            total_transactions = result["total"] or 0

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM transactions
            WHERE status = 'Normal'
            """
        )
        result = cursor.fetchone()

        if result:
            normal_transactions = result["total"] or 0

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM transactions
            WHERE status = 'Fraud'
            """
        )
        result = cursor.fetchone()

        if result:
            fraud_transactions = result["total"] or 0

        cursor.execute(
            """
            SELECT COALESCE(SUM(transaction_amount), 0) AS total
            FROM transactions
            WHERE status = 'Normal'
            """
        )
        result = cursor.fetchone()

        if result:
            total_revenue = result["total"] or 0

        cursor.execute(
            """
            SELECT COALESCE(SUM(transaction_amount), 0) AS total
            FROM transactions
            WHERE status = 'Fraud'
            """
        )
        result = cursor.fetchone()

        if result:
            fraud_loss = result["total"] or 0

        cursor.execute(
            """
            SELECT
                id, vehicle_number, toll_plaza,
                transaction_amount, transaction_time, status
            FROM transactions
            ORDER BY id DESC
            """
        )
        report_transactions = cursor.fetchall()

    except mysql.connector.Error as error:
        print("Reports error:", error)
        flash("Unable to load reports.", "danger")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template(
        "reports.html",
        total=total_transactions,
        normal=normal_transactions,
        fraud=fraud_transactions,
        total_revenue=total_revenue,
        fraud_loss=fraud_loss,
        transactions=report_transactions
    )


# =========================================================
# VEHICLES PAGE
# =========================================================

@app.route("/vehicles", methods=["GET", "POST"])
@login_required
def vehicles_page():

    if request.method == "POST":

        vehicle_number = request.form.get(
            "vehicle_number", ""
        ).strip().upper()

        vehicle_type = request.form.get(
            "vehicle_type", ""
        ).strip()

        owner_name = request.form.get(
            "owner_name", ""
        ).strip()

        if not vehicle_number:
            flash("Please enter a vehicle number.", "warning")
            return redirect(url_for("vehicles_page"))

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT id
                FROM vehicles
                WHERE vehicle_number = %s
                """,
                (vehicle_number,)
            )

            if cursor.fetchone():
                flash("This vehicle is already registered.", "warning")
                return redirect(url_for("vehicles_page"))

            cursor.execute(
                """
                INSERT INTO vehicles
                (vehicle_number, vehicle_type, owner_name)
                VALUES (%s, %s, %s)
                """,
                (vehicle_number, vehicle_type, owner_name)
            )

            connection.commit()
            flash("Vehicle added successfully.", "success")

        except mysql.connector.Error as error:
            if connection:
                connection.rollback()

            print("Vehicles page error:", error)
            flash("Unable to add vehicle.", "danger")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return redirect(url_for("vehicles_page"))

    vehicles = []
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id, vehicle_number, vehicle_type,
                owner_name, created_at
            FROM vehicles
            ORDER BY id DESC
            """
        )

        vehicles = cursor.fetchall()

    except mysql.connector.Error as error:
        print("Load vehicles error:", error)
        flash("Unable to load vehicles.", "danger")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template(
        "vehicles.html",
        vehicles=vehicles
    )


# =========================================================
# TOLL PLAZAS PAGE
# =========================================================

@app.route("/toll-plazas", methods=["GET", "POST"])
@login_required
def toll_plazas_page():

    if request.method == "POST":

        plaza_name = request.form.get(
            "plaza_name", ""
        ).strip()

        location = request.form.get(
            "location", ""
        ).strip()

        toll_amount_text = request.form.get(
            "toll_amount", "0"
        ).strip()

        if not plaza_name:
            flash("Please enter a toll plaza name.", "warning")
            return redirect(url_for("toll_plazas_page"))

        try:
            toll_amount = float(toll_amount_text or 0)
        except ValueError:
            flash("Please enter a valid toll amount.", "danger")
            return redirect(url_for("toll_plazas_page"))

        if toll_amount < 0:
            flash("Toll amount cannot be negative.", "danger")
            return redirect(url_for("toll_plazas_page"))

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT id
                FROM toll_plazas
                WHERE LOWER(plaza_name) = LOWER(%s)
                """,
                (plaza_name,)
            )

            if cursor.fetchone():
                flash("This toll plaza already exists.", "warning")
                return redirect(url_for("toll_plazas_page"))

            cursor.execute(
                """
                INSERT INTO toll_plazas
                (plaza_name, location, toll_amount)
                VALUES (%s, %s, %s)
                """,
                (plaza_name, location, toll_amount)
            )

            connection.commit()
            flash("Toll plaza added successfully.", "success")

        except mysql.connector.Error as error:
            if connection:
                connection.rollback()

            print("Toll plaza error:", error)
            flash("Unable to add toll plaza.", "danger")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return redirect(url_for("toll_plazas_page"))

    toll_plazas = []
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id, plaza_name, location,
                toll_amount, created_at
            FROM toll_plazas
            ORDER BY id DESC
            """
        )

        toll_plazas = cursor.fetchall()

    except mysql.connector.Error as error:
        print("Load toll plazas error:", error)
        flash("Unable to load toll plazas.", "danger")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template(
        "toll_plazas.html",
        toll_plazas=toll_plazas
    )


# =========================================================
# USERS PAGE
# =========================================================

@app.route("/users")
@login_required
def users_page():

    users = []
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, name, email, role, created_at
            FROM users
            ORDER BY id DESC
            """
        )

        users = cursor.fetchall()

    except mysql.connector.Error as error:
        print("Users page error:", error)
        flash("Unable to load users.", "danger")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template(
        "users.html",
        users=users
    )


# =========================================================
# NOTIFICATIONS PAGE
# =========================================================

@app.route("/notifications")
@login_required
def notifications_page():

    notifications = []
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id, title, message, notification_type,
                is_read, created_at
            FROM notifications
            ORDER BY id DESC
            """
        )

        notifications = cursor.fetchall()

    except mysql.connector.Error as error:
        print("Notifications page error:", error)
        flash("Unable to load notifications.", "danger")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template(
        "notifications.html",
        notifications=notifications
    )


# =========================================================
# CREATE DEFAULT ADMIN
# =========================================================

def create_default_admin():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(email) = %s
            """,
            ("admin@toll.com",)
        )

        existing_admin = cursor.fetchone()

        if not existing_admin:

            hashed_password = generate_password_hash(
                "admin123"
            )

            cursor.execute(
                """
                INSERT INTO users
                (name, email, password, role)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    "System Administrator",
                    "admin@toll.com",
                    hashed_password,
                    "admin"
                )
            )

            connection.commit()

            print("Default admin account created.")

    except mysql.connector.Error as error:
        print("Create admin error:", error)

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    if not os.environ.get("DB_PASSWORD"):
        print(
            "WARNING: Set DB_PASSWORD in this terminal "
            "before starting the app."
        )

    if app.secret_key == "CHANGE_THIS_SECRET_KEY_BEFORE_RUNNING":
        print(
            "WARNING: Set FLASK_SECRET_KEY to a long random value "
            "before starting the app."
        )

    create_default_admin()

    app.run(debug=True)
