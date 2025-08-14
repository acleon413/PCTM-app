from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.orm import sessionmaker
import os

# ==== CONFIGURATION ====
# Path to your SQLite database file
SQLITE_FILE = os.path.abspath(os.path.join("instance", "database.db"))

# PostgreSQL connection string: change username, password, dbname, host as needed
POSTGRES_URL = "postgresql+psycopg2://myuser:mypassword@localhost/mydb"

# ==== SETUP ENGINES ====
sqlite_engine = create_engine(f"sqlite:///{SQLITE_FILE}")
pg_engine = create_engine(POSTGRES_URL)

# ==== LOAD METADATA FROM SQLITE ====
metadata = MetaData()
metadata.reflect(bind=sqlite_engine)

# ==== CONVERT DATETIME COLUMNS TO TIMESTAMP FOR POSTGRESQL ====
for table in metadata.tables.values():
    for column in table.columns:
        if column.type.__class__.__name__ == "DATETIME":
            column.type = DateTime()

# ==== CREATE TABLES IN POSTGRES ====
metadata.create_all(pg_engine)

# ==== CREATE SESSIONS ====
SQLiteSession = sessionmaker(bind=sqlite_engine)
PGSession = sessionmaker(bind=pg_engine)

sqlite_session = SQLiteSession()
pg_session = PGSession()

# ==== COPY DATA TABLE-BY-TABLE ====
for table in metadata.sorted_tables:
    print(f"Copying table {table.name}...")
    rows = list(sqlite_session.execute(table.select()))
    if rows:
        dict_rows = [dict(row._mapping) for row in rows]
        pg_session.execute(table.insert(), dict_rows)

pg_session.commit()
sqlite_session.close()
pg_session.close()

print("✅ Migration complete!")
