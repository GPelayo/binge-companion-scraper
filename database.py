from binge_models.models import Series
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config import RDB_DATABASE_NAME, RDB_HOST, RDB_PASSWORD, RDB_USER


Base = declarative_base()


class Database:
    def __init__(self):
        engine = create_engine(f"postgresql://{RDB_USER}:{RDB_PASSWORD}@{RDB_HOST}:5432/{RDB_DATABASE_NAME}")
        self.session_maker = sessionmaker(bind=engine)
        self.session = self.session_maker()

    def has_series(self, series_id: str) -> bool:
        series = self.session.execute(text(f"SELECT 1 FROM series WHERE '{series_id}' = series.series_id"))
        return series is None

    def write_series(self, series: Series):
        self.session.add(series)
        self.session.commit()

    def __enter__(self) -> 'Database':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
