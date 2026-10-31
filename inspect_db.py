import db

def inspect():
    conn = db.get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SHOW TABLES")
    tables = [list(r.values())[0] for r in cur.fetchall()]
    print("Database:", conn.database)
    print("Total tables:", len(tables))
    print("Tables list:", tables)
    print()

    for t in tables:
        cur.execute(f"SELECT COUNT(*) as cnt FROM {t}")
        cnt = cur.fetchone()['cnt']
        print(f"==================================================")
        print(f"TABLE: {t} (Row count: {cnt})")
        print(f"==================================================")
        cur.execute(f"DESCRIBE {t}")
        for col in cur.fetchall():
            print(f"  {col['Field']:25} {col['Type']:20} Null:{col['Null']:4} Key:{col['Key']:4} Default:{str(col['Default']):10} Extra:{col['Extra']}")

        # Foreign keys
        cur.execute("""
            SELECT COLUMN_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND REFERENCED_TABLE_NAME IS NOT NULL
        """, (t,))
        fks = cur.fetchall()
        if fks:
            print("  Foreign Keys:")
            for fk in fks:
                print(f"    {fk['COLUMN_NAME']} -> {fk['REFERENCED_TABLE_NAME']}({fk['REFERENCED_COLUMN_NAME']}) [{fk['CONSTRAINT_NAME']}]")

        # Constraints
        cur.execute("""
            SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE
            FROM information_schema.TABLE_CONSTRAINTS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        """, (t,))
        constraints = cur.fetchall()
        if constraints:
            print("  Table Constraints:")
            for c in constraints:
                print(f"    {c['CONSTRAINT_NAME']} ({c['CONSTRAINT_TYPE']})")
        print()

    cur.close()
    conn.close()

if __name__ == "__main__":
    inspect()

