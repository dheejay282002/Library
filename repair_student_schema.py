import sqlite3

REQUIRED = {
    "email": "ALTER TABLE library_student ADD COLUMN email varchar(255)",
    "birthday": "ALTER TABLE library_student ADD COLUMN birthday date",
    "address": "ALTER TABLE library_student ADD COLUMN address varchar(255) NOT NULL DEFAULT ''",
    "guardian_name": "ALTER TABLE library_student ADD COLUMN guardian_name varchar(100) NOT NULL DEFAULT ''",
    "current_address": "ALTER TABLE library_student ADD COLUMN current_address varchar(255) NOT NULL DEFAULT ''",
    "is_rejected": "ALTER TABLE library_student ADD COLUMN is_rejected bool NOT NULL DEFAULT 0",
}


def main() -> None:
    con = sqlite3.connect("db.sqlite3")
    cur = con.cursor()

    cur.execute("PRAGMA table_info('library_student')")
    existing = {row[1] for row in cur.fetchall()}

    added = []
    for column, sql in REQUIRED.items():
        if column not in existing:
            cur.execute(sql)
            added.append(column)

    cur.execute(
        "CREATE INDEX IF NOT EXISTS library_student_email_idx ON library_student(email)"
    )

    cur.execute("PRAGMA table_info('library_student')")
    columns = [row[1] for row in cur.fetchall()]

    con.commit()
    con.close()
    print(f"added columns: {added}")
    print(f"student columns: {columns}")


if __name__ == "__main__":
    main()
