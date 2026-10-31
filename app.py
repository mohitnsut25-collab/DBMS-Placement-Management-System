from datetime import date, datetime
from decimal import Decimal
from flask import Flask, jsonify, render_template, request
from flask.json.provider import DefaultJSONProvider

from db import get_db_connection
from routes import (
    department_bp,
    student_bp,
    company_bp,
    job_bp,
    application_bp,
    interview_bp,
    offer_bp,
    database_design_bp
)


class CustomJSONProvider(DefaultJSONProvider):
    """Custom JSON provider to correctly serialize date, datetime, and Decimal values."""
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


app = Flask(__name__)
app.json_provider_class = CustomJSONProvider
app.json = CustomJSONProvider(app)

# Register Blueprints for all entities and documentation
app.register_blueprint(department_bp)
app.register_blueprint(student_bp)
app.register_blueprint(company_bp)
app.register_blueprint(job_bp)
app.register_blueprint(application_bp)
app.register_blueprint(interview_bp)
app.register_blueprint(offer_bp)
app.register_blueprint(database_design_bp)


# Global Error Handlers
@app.errorhandler(404)
def handle_404(e):
    if request.path.startswith("/api/"):
        return jsonify({
            "success": False,
            "error": "The requested API resource or endpoint was not found."
        }), 404
    return jsonify({
        "success": False,
        "error": "The requested page was not found."
    }), 404


@app.errorhandler(405)
def handle_405(e):
    return jsonify({
        "success": False,
        "error": "HTTP method not allowed for the requested URL."
    }), 405


@app.errorhandler(500)
def handle_500(e):
    app.logger.exception("Unhandled server error")
    return jsonify({
        "success": False,
        "error": "An internal server error occurred."
    }), 500


# ============================================================================
# Frontend View Routes (HTML Jinja Templates)
# ============================================================================

@app.route("/")
def home():
    """Main administrative dashboard view."""
    return render_template("dashboard.html", active_page="dashboard")


@app.route("/departments")
def departments_view():
    """Academic department master data view."""
    return render_template("departments.html", active_page="departments")


@app.route("/students")
def students_view():
    """Student profiles and multiple contact numbers master data view."""
    return render_template("students.html", active_page="students")


@app.route("/companies")
def companies_view():
    """Corporate recruiting partners and HR contacts master data view."""
    return render_template("companies.html", active_page="companies")


@app.route("/jobs")
def jobs_view():
    """Campus recruitment job vacancies view."""
    return render_template("jobs.html", active_page="jobs")


@app.route("/applications")
def applications_view():
    """Student application pipeline and progression view."""
    return render_template("applications.html", active_page="applications")


@app.route("/interviews")
def interviews_view():
    """Interview assessment rounds management view."""
    return render_template("interviews.html", active_page="interviews")


@app.route("/offers")
def offers_view():
    """Placement offers and acceptance tracking view."""
    return render_template("offers.html", active_page="offers")


@app.route("/database-design")
def database_design_view():
    """Dedicated Database Design & DBMS Analysis view."""
    return render_template("database_design.html", active_page="database_design")


# ============================================================================
# API Health Check Endpoint (Preserved and Enhanced for 10 Tables)
# ============================================================================

@app.route("/api/health")
def database_health():
    """Test MySQL connection and verify table detection."""
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Check database details
        cursor.execute("SELECT DATABASE(), VERSION()")
        result = cursor.fetchone()

        database_name = result[0]
        mysql_version = result[1]

        # Retrieve all ten tables
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]

        return jsonify({
            "status": "Connected Successfully",
            "database": database_name,
            "mysql_version": mysql_version,
            "tables": tables,
            "total_tables": len(tables)
        })

    except Exception:
        app.logger.exception("Database connection failed")
        return jsonify({
            "status": "Connection Failed",
            "message": "Check the Flask terminal for details."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# Run Flask application
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
