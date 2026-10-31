"""
Database Backup Utility
Generates full SQL and JSON backups of placement_recruitment_db prior to schema migration.
"""

import os
import sys
import json
from datetime import date, datetime
from decimal import Decimal

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import db

def custom_serializer(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def perform_backup():
    conn = db.get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SHOW TABLES")
    tables = [list(r.values())[0] for r in cur.fetchall()]

    sql_statements = [
        "-- --------------------------------------------------------",
        "-- Backup of database: placement_recruitment_db",
        f"-- Generated at: {datetime.now().isoformat()}",
        "-- --------------------------------------------------------\n"
    ]

    json_backup = {}

    for t in tables:
        # Table structure
        cur.execute(f"SHOW CREATE TABLE {t}")
        create_res = cur.fetchone()
        create_sql = list(create_res.values())[1]
        sql_statements.append(f"-- Table structure for table `{t}`")
        sql_statements.append(f"{create_sql};\n")

        # Table data
        cur.execute(f"SELECT * FROM {t}")
        rows = cur.fetchall()
        json_backup[t] = rows

        if rows:
            sql_statements.append(f"-- Dumping data for table `{t}`")
            cols = list(rows[0].keys())
            cols_str = ", ".join([f"`{c}`" for c in cols])
            
            for row in rows:
                val_parts = []
                for c in cols:
                    v = row[c]
                    if v is None:
                        val_parts.append("NULL")
                    elif isinstance(v, (int, float, Decimal)):
                        val_parts.append(str(v))
                    elif isinstance(v, (date, datetime)):
                        val_parts.append(f"'{v.isoformat()}'")
                    else:
                        escaped = str(v).replace("\\", "\\\\").replace("'", "\\'")
                        val_parts.append(f"'{escaped}'")
                sql_statements.append(f"INSERT INTO `{t}` ({cols_str}) VALUES ({', '.join(val_parts)});")
            sql_statements.append("\n")

    # Write SQL backup
    sql_path = "database_backup/pre_upgrade_backup.sql"
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_statements))
    print(f"SQL backup written to {sql_path}")

    # Write JSON backup
    json_path = "database_backup/pre_upgrade_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_backup, f, indent=2, default=custom_serializer)
    print(f"JSON backup written to {json_path}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    perform_backup()
