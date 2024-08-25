import asyncio
import os.path
from contextlib import contextmanager

import sqlalchemy as sa

import pandas as pd

from app.util import get_location


def get_uta(
        *,
        version: str,
        dl_url="https://dl.biocommons.org/uta"
):
    print("Checking for UTA database")

    # Check if UTA database exists
    if (os.path.exists(os.path.join(
            get_location(), "data", f"{version}.pgd.gz"
    )) or os.path.exists(
        os.path.join(get_location(), "data", f"{version}.sql.gz"
                     ))):
        print("UTA database found, skipping download")
        return

    print("UTA database not found, downloading")
    # Download UTA database

    os.makedirs(os.path.join(get_location(), "data"), exist_ok=True)

    for f in ["", ".sha1"]:
        filename = f"{version}.pgd.gz{f}"

        fullpath_name = os.path.join(get_location(), "data", filename)

        os.system(
            f"cd data && test -e {os.path.join(fullpath_name)} || curl -O {dl_url}/{filename}"
        )


def rename_and_unzip(*, version: str):
    print("Renaming the UTA dump to .sql.gz")

    # rename {version}.pgd.gz to {version}.sql.gz if it exists otherwise skip
    if os.path.exists(
            os.path.join(get_location(), "data", f"{version}.pgd.gz")):
        os.rename(
            os.path.join(get_location(), "data", f"{version}.pgd.gz"),
            os.path.join(get_location(), "data", f"{version}.sql.gz"),
        )
    else:
        print("No .pgd.gz file found, skipping renaming")

    print("Unzipping the UTA dump if not already unzipped")

    # Unzip the UTA dump
    if os.path.exists(os.path.join(get_location(), "data", f"{version}.sql")):
        print("UTA dump already unzipped, skipping")
        return

    os.system(
        f"cd data && gunzip {os.path.join(get_location(), 'data', f'{version}.sql.gz')}"
    )


def strip_whitespace_lines(string: str) -> str:
    return "\n".join([line.strip() for line in string.split("\n")])


def setup_roles(
        *,
        sql_dir: str
):
    print("Setting up roles for UTA database")

    # Create roles for UTA database
    with open(os.path.join(sql_dir, "01_roles.sql"), "w") as f:
        f.write(
            strip_whitespace_lines(
                """
                CREATE ROLE anonymous;
                ALTER ROLE anonymous WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB NOLOGIN NOREPLICATION NOBYPASSRLS;
                CREATE ROLE uta_admin;
                ALTER ROLE uta_admin WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB NOLOGIN NOREPLICATION NOBYPASSRLS;
                """)
        )


def setup_schema_head(
        *,
        sql_dir: str,
        version: str
):
    print("Extracting all sql commands before the first COPY command")

    with open(os.path.join(get_location(), "data", f"{version}.sql"),
              "r") as f:
        with open(os.path.join(sql_dir, "02_schema_head.sql"), "w") as f2:
            for line in f:
                if "COPY" in line:
                    break
                f2.write(line)


def add_data(
        *,
        version: str,
        sql_dir: str,
        genes: list[str]
):
    print(f"Adding selected data from {genes} to the database")

    all_genes = genes.__str__().replace("[", "(").replace("]", ")")

    os.makedirs(os.path.join(sql_dir, "data"), exist_ok=True)

    with open(os.path.join(sql_dir, "03_data.sql"), "w") as f:
        with get_engine() as engine:
            pd.read_sql(
                f"""
                SELECT o.origin_id, o.name, o.descr, o.updated, o.url, o.url_ac_fmt
                FROM {version}.origin o
                """,
                engine,
                dtype={
                    "origin_id": 'Int64',
                    "name": str,
                    "descr": str,
                    "updated": str,
                    "url": str,
                    "url_ac_fmt": str
                }
            ).to_csv(
                os.path.join(sql_dir, "data", "origin.csv"),
                index=False
            )

            pd.read_sql(
                f"""
                SELECT m.key, m.value
                FROM {version}.meta m
                """,
                engine,
                dtype={
                    "key": str,
                    "value": str
                }
            ).to_csv(
                os.path.join(sql_dir, "data", "meta.csv"),
                index=False
            )

            pd.read_sql(
                f"""
                SELECT g.hgnc, g.maploc, g.descr, g.summary, g.aliases, g.added
                FROM {version}.gene g
                WHERE g.hgnc IN {all_genes}
                """,
                engine,
                dtype={
                    "hgnc": str,
                    "maploc": str,
                    "descr": str,
                    "summary": str,
                    "aliases": str,
                    "added": str,
                }
            ).to_csv(
                os.path.join(sql_dir, "data", "genes.csv"),
                index=False
            )

            protein_ac_subquery = f"""
            SELECT pro_ac AS ac
            FROM {version}.associated_accessions
            WHERE tx_ac IN (
                SELECT ac
                FROM {version}.transcript
                WHERE hgnc IN {all_genes}
            )
            UNION
            SELECT alt_ac AS ac
            FROM {version}.exon_set
            WHERE tx_ac IN (
                SELECT ac
                FROM {version}.transcript
                WHERE hgnc IN {all_genes}
            )
            """

            pd.read_sql(
                f"""
                SELECT t.ac, t.origin_id, t.hgnc, t.cds_start_i, t.cds_end_i, t.cds_md5, t.added
                FROM {version}.transcript t
                WHERE hgnc in {all_genes}
                OR ac IN (
                    {protein_ac_subquery}
                )
                """,
                engine,
                dtype={
                    "ac": str,
                    "origin_id": 'Int64',
                    "hgnc": str,
                    "cds_start_i": 'Int64',
                    "cds_end_i": 'Int64',
                    "cds_md5": str,
                    "added": str,
                }
            ).to_csv(
                os.path.join(sql_dir, "data", "transcripts.csv"),
                index=False
            )

            pd.read_sql(
                f"""
                SELECT s.seq_anno_id, s.seq_id, s.origin_id, s.ac, s.descr, s.added
                FROM {version}.seq_anno s
                WHERE ac IN (SELECT ac FROM {version}.transcript WHERE hgnc IN {all_genes})
                OR ac IN (
                    {protein_ac_subquery}
                )
                """,
                engine,
                dtype={
                    "seq_anno_id": 'Int64',
                    "seq_id": str,
                    "origin_id": 'Int64',
                    "ac": str,
                    "descr": str,
                    "added": str,
                }
            ).to_csv(
                os.path.join(sql_dir, "data", "seq_anno.csv"),
                index=False
            )

            # psql-uta "select seq_id from seq where seq_id in (select seq_id from seq_anno where ac in (select ac from transcript where hgnc in $PG_GENES));" >download/seq.tsv
            pd.read_sql(
                f"""
                SELECT s.seq_id, s.len, s.seq
                FROM {version}.seq s
                WHERE seq_id IN (
                    SELECT seq_id
                    FROM {version}.seq_anno
                    WHERE ac IN (
                        SELECT ac
                        FROM {version}.transcript
                        WHERE hgnc IN {all_genes}
                    ) OR ac IN (
                        {protein_ac_subquery}
                    )
                )
                """,
                engine,
                dtype={
                    "seq_id": str,
                    "len": 'Int64',
                    "seq": str
                }

            ).to_csv(
                os.path.join(sql_dir, "data", "seq.csv"),
                index=False
            )

            # psql-uta "select associated_accession_id from associated_accessions where tx_ac in (select ac from transcript where hgnc in $PG_GENES);" >download/associated_accessions.tsv
            pd.read_sql(
                f"""
                SELECT a.associated_accession_id, a.tx_ac, a.pro_ac, a.origin, a.added
                FROM {version}.associated_accessions a
                WHERE tx_ac IN (
                    SELECT ac
                    FROM {version}.transcript
                    WHERE hgnc IN {all_genes}
                )
                """,
                engine,
                dtype={
                    "associated_accession_id": 'Int64',
                    "tx_ac": str,
                    "pro_ac": str,
                    "origin": str,
                    "added": str,
                }
            ).to_csv(
                os.path.join(sql_dir, "data", "associated_accessions.csv"),
                index=False
            )

            # psql-uta "select exon_set_id from exon_set where tx_ac in (select ac from transcript where hgnc in $PG_GENES);" >download/exon_set.tsv
            pd.read_sql(
                f"""
                SELECT 
                    e.exon_set_id,
                    e.tx_ac,
                    e.alt_ac,
                    e.alt_strand,
                    e.alt_aln_method,
                    e.added
                FROM {version}.exon_set e
                WHERE tx_ac IN (
                    SELECT ac
                    FROM {version}.transcript
                    WHERE hgnc IN {all_genes}
                ) 
                """,
                engine,
                dtype={
                    "exon_set_id": 'Int64',
                    "tx_ac": str,
                    "alt_ac": str,
                    "alt_strand": 'Int64',
                    "alt_aln_method": str,
                    "added": str,
                }
            ).to_csv(
                os.path.join(sql_dir, "data", "exon_set.csv"),
                index=False
            )

            # psql-uta "select exon_id from exon where exon_set_id in (select exon_set_id from exon_set where tx_ac in (select ac from transcript where hgnc in $PG_GENES));" >download/exon.tsv
            pd.read_sql(
                f"""
                SELECT 
                    e.exon_id,
                    e.exon_set_id,
                    e.start_i,
                    e.end_i,
                    e.ord,
                    e.name
                FROM {version}.exon e
                WHERE exon_set_id IN (
                    SELECT exon_set_id
                    FROM {version}.exon_set
                    WHERE tx_ac IN (
                        SELECT ac
                        FROM {version}.transcript
                        WHERE hgnc IN {all_genes}
                    )
                )
                """,
                engine,
                dtype={
                    "exon_id": 'Int64',
                    "exon_set_id": 'Int64',
                    "start_i": 'Int64',
                    "end_i": 'Int64',
                    "ord": 'Int64',
                    "name": str
                }
            ).to_csv(
                os.path.join(sql_dir, "data", "exon.csv"),
                index=False
            )

            # psql-uta "select exon_aln_id from exon_aln where tx_exon_id in (select exon_id from exon where exon_set_id in (select exon_set_id from exon_set where tx_ac in (select ac from transcript where hgnc in $PG_GENES)));" >download/exon_aln.tsv
            pd.read_sql(
                f"""
                SELECT 
                    e.exon_aln_id,
                    e.tx_exon_id,
                    e.alt_exon_id,
                    e.cigar,
                    e.added,
                    e.tx_aseq,
                    e.alt_aseq
                FROM {version}.exon_aln e
                WHERE tx_exon_id IN (
                    SELECT exon_id
                    FROM {version}.exon
                    WHERE exon_set_id IN (
                        SELECT exon_set_id
                        FROM {version}.exon_set
                        WHERE tx_ac IN (
                            SELECT ac
                            FROM {version}.transcript
                            WHERE hgnc IN {all_genes}
                        )
                    )
                )
                """,
                engine,
                dtype={
                    "exon_aln_id": 'Int64',
                    "tx_exon_id": 'Int64',
                    "alt_exon_id": 'Int64',
                    "cigar": str,
                    "added": str,
                    "tx_aseq": str,
                    "alt_aseq": str
                }
            ).to_csv(
                os.path.join(sql_dir, "data", "exon_aln.csv"),
                index=False
            )

            # make it load data from the csv file
            f.write(
                strip_whitespace_lines(
                    f"""
                    \\COPY {version}.meta FROM '/docker-entrypoint-initdb.d/data/meta.csv' DELIMITER ',' CSV HEADER;
                    \\COPY {version}.origin FROM '/docker-entrypoint-initdb.d/data/origin.csv' DELIMITER ',' CSV HEADER;
                    \\COPY {version}.gene FROM '/docker-entrypoint-initdb.d/data/genes.csv' DELIMITER ',' CSV HEADER;
                    \\COPY {version}.transcript FROM '/docker-entrypoint-initdb.d/data/transcripts.csv' DELIMITER ',' CSV HEADER;
                    \\COPY {version}.seq_anno FROM '/docker-entrypoint-initdb.d/data/seq_anno.csv' DELIMITER ',' CSV HEADER;
                    \\COPY {version}.seq FROM '/docker-entrypoint-initdb.d/data/seq.csv' DELIMITER ',' CSV HEADER;
                    \\COPY {version}.associated_accessions FROM '/docker-entrypoint-initdb.d/data/associated_accessions.csv' DELIMITER ',' CSV HEADER;
                    \\COPY {version}.exon_set FROM '/docker-entrypoint-initdb.d/data/exon_set.csv' DELIMITER ',' CSV HEADER;
                    \\COPY {version}.exon FROM '/docker-entrypoint-initdb.d/data/exon.csv' DELIMITER ',' CSV HEADER;
                    \\COPY {version}.exon_aln FROM '/docker-entrypoint-initdb.d/data/exon_aln.csv' DELIMITER ',' CSV HEADER;
                    """
                )
            )


def setup_schema_tail(
        *,
        sql_dir: str,
        version: str
):
    print("Extracting tail of UTA database dump from ALTER TABLE onwards")

    with open(os.path.join(sql_dir, "04_schema.sql"), "w") as f:
        f.write("")

    os.system(
        f"""
        cd {sql_dir} &&
        tail -1000 "../download/{version}.sql" | \
        awk '/ALTER TABLE / {{found=1}} found {{print}}' > 04_schema.sql
        """
    )


def setup_db(
        *,
        sql_dir: str,
        version: str,
):
    print("Renaming the table to uta")

    with open(os.path.join(sql_dir, "05_db.sql"), "w") as f:
        f.write(
            strip_whitespace_lines(
                f"""
                ALTER SCHEMA {version} RENAME TO uta;
                """
            )
        )


def reset_postgres(
):
    # require user confirmation
    print(
        "Resetting the postgres database. Press 'Y' to confirm, any other key to cancel")

    if input().lower() != "y":
        print("Reset cancelled")
        return

    print("Resetting the postgres database")

    os.system(
        f"cd {os.path.join(get_location(), "..")} && docker-compose down -v"
    )

    print("Removed old database and volumes")

    os.system(
        f"cd {os.path.join(get_location(), "..")} && docker-compose up -d"
    )


@contextmanager
def get_engine():
    engine = None
    try:
        engine = sa.create_engine(
            url="postgresql://anonymous:anonymous@uta.biocommons.org/uta",
        )
        print("Successfully connected to UTA database")
        yield engine
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if engine:
            engine.dispose()


async def main():
    VERSION = "uta_20210129"
    genes = ["RYR2", ]

    get_uta(version=VERSION)
    rename_and_unzip(version=VERSION)

    os.makedirs(os.path.join(get_location(), "sql"), exist_ok=True)
    sql_dir = os.path.join(get_location(), "sql")

    setup_roles(
        sql_dir=sql_dir
    )
    setup_schema_head(
        sql_dir=sql_dir,
        version=VERSION
    )
    add_data(
        sql_dir=sql_dir,
        genes=genes,
        version=VERSION
    )
    setup_schema_tail(
        sql_dir=sql_dir,
        version=VERSION
    )
    setup_db(
        sql_dir=sql_dir,
        version=VERSION
    )

    reset_postgres()


if __name__ == "__main__":
    asyncio.run(main())
