import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from pydantic import (
    DirectoryPath,
    Field,
    HttpUrl,
    PostgresDsn,
    computed_field,
    FilePath,
)
from pydantic_settings import BaseSettings

from cpvt_website_models.util import get_location, mkdir_p


class SqlFiles(BaseSettings):
    sql_dir: DirectoryPath = os.path.join(get_location(), "loaders/views")

    @computed_field
    @property
    def sql_files(self) -> list[FilePath]:
        # return an array of all the files that end with .sql in lexicographical order
        # in the sql_dir
        return sorted(
            [
                Path(os.path.join(self.sql_dir, f))
                for f in os.listdir(self.sql_dir)
                if f.endswith(".sql")
            ]
        )

    class Config:
        env_file = os.path.join(get_location(), "../.env")
        env_file_encoding = "utf-8"
        extra = "ignore"


class Settings(BaseSettings):
    database_file: str = "Database_3_13.xlsx"
    database_file_dna_refseq: str = "NM_001035.3"
    database_file_protein_refseq: str = "NP_001026.2"
    ryr_hgnc_id: str = "HGNC:10484"

    exon_span_file: str = "uniprot_Q92736.xlsx"
    structure_span_file: str = "ryr2_subdomains.xlsx"

    data_dir: str = os.path.join(get_location(), "../data")
    output_dir: str = os.path.join(get_location(), "../output")
    save_dir_name: str | None = None

    reset_database: bool = False
    alembic_base_revision: str = "1f355f80cd00"

    # data
    @computed_field()
    @property
    def database_excel(self) -> str:
        return os.path.join(self.data_dir, self.database_file)

    @computed_field()
    @property
    def exon_span_excel(self) -> str:
        return os.path.join(self.data_dir, self.exon_span_file)

    @computed_field()
    @property
    def structure_excel(self) -> str:
        return os.path.join(self.data_dir, self.structure_span_file)

    # PostgreSQL
    postgresql_host: str = "localhost"
    postgresql_username: str = "postgres"
    postgresql_password: str = "postgres"
    postgresql_database: str = "postgres"
    postgresql_schema: str = "public"
    postgresql_port: int = 5432

    # HGVS postgres
    hgvs_postgresql_schema: str = "uta"

    nih_api_key: str | None = None

    @computed_field
    @property
    def postgresql_dsn(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.postgresql_username,
            password=self.postgresql_password,
            host=self.postgresql_host,
            port=self.postgresql_port,
            path=self.postgresql_database,
        )

    @computed_field
    @property
    def hgvs_postgresql_url(self) -> str:
        return (
            f"postgresql://"
            f"{self.postgresql_username}:"
            f"{self.postgresql_password}@"
            f"{self.postgresql_host}:"
            f"{self.postgresql_port}/"
            f"{self.postgresql_database}/"
            f"{self.hgvs_postgresql_schema}"
        )

    # hgvs
    hgvs_seqrepo_dir: DirectoryPath

    # Sqlite
    sqlite_database: str = "sqlite.db"

    @computed_field
    @property
    def sqlite_dsn(self) -> str:
        location = get_location()

        data_dir = os.path.join(location, "../data/schema1-11")

        mkdir_p(data_dir)

        return f"sqlite:///{os.path.join(data_dir, self.sqlite_database)}"

    # sqlalchemy
    target_databases: list[TargetDatabase] = list()
    sqlalchemy_echo: bool = True
    n_conn: int = 50

    # logging
    max_print_length: int = Field(100, gt=0)

    # processing
    nlp_similarity_threshold: float = Field(0.9, gt=0, lt=1)
    nlp_model: str = "en_core_web_lg"

    # CLINVAR mutations
    mutation_data_url: HttpUrl = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited//variant_summary.txt.gz"
    mutation_data_md5_url: HttpUrl = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited//variant_summary.txt.gz.md5"
    clinvar_dir: str = os.path.join(get_location(), "../data/clinvar")

    """
    The directory relative to the data directory where the clinvar data is stored.
    Use "." to store the data in the data directory itself.
    """
    clinvar_mutation_file: str = "clinvar.duckdb"

    # @computed_field
    # @property
    # def clinvar_dir(self) -> str:
    #     return os.path.join(self.data_dir, self._clinvar_dir)

    @computed_field
    @property
    def clinvar_mutation_file_path(self) -> str:
        return os.path.join(
            self.data_dir, self.clinvar_dir, self.clinvar_mutation_file
        )

    gene_refseq: str = "NM_001035.3"
    """
    The gene refseq to use for the conversion of g to c coordinates. 
    Defaults to NM_001035.3 (RYR2)
    """

    # apache age graph database
    graph_database: str = "sequence_variant_projections"

    grammar_file: FilePath = Path(
        get_location(), "models/variants/hgvs/hgvs_types.pymeta"
    )

    @computed_field()
    @property
    def tmp_dir(self) -> str:
        t_dir = os.path.join(self.output_dir, "tmp")
        mkdir_p(t_dir)
        return t_dir

    @computed_field()
    @property
    def save_dir(self) -> str:
        save_dir_name = self.save_dir_name
        if save_dir_name is None:
            print(
                cf.orange(
                    "No save directory name specified. Using current date"
                )
            )
            save_dir_name = datetime.now().strftime("%Y-%m-%d")

        s_dir = os.path.join(self.output_dir, save_dir_name)
        mkdir_p(s_dir)
        return s_dir

    class Config:
        env_file = os.path.join(get_location(), "../.env")
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    print("Loading settings...")
    settings = Settings()
    set_env_for_hgvs(settings)
    return settings


@lru_cache()
def get_sql_files() -> SqlFiles:
    print("Loading sql files...")
    sql_files = SqlFiles()
    return sql_files


@lru_cache()
def get_sqlite_files() -> SqliteFiles:
    print("Loading sqlite files...")
    sqlite_files = SqliteFiles()
    return sqlite_files


__all__ = [
    "Settings",
    "TargetDatabase",
    "get_settings",
    "get_sql_files",
    "get_sqlite_files",
]
