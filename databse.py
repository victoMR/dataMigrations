from sqlalchemy import create_engine
from config import DatabaseConfig
import pandas as pd
from typing import Tuple

class DatabaseManager:
  @staticmethod
  def create_postgres_engine(config: DatabaseConfig):
    return create_engine(
      f'postgresql://{config.username}:{config.password}'
      f'@{config.host}:{config.port}/{config.database}'
    )

  @staticmethod
  def create_sqlserver_engine(config: DatabaseConfig):
    return create_engine(
      f"mssql+pyodbc://{config.username}:{config.password}"
      f"@{config.host}:{config.port}/{config.database}"
      f"?driver=ODBC+Driver+17+for+SQL+Server"
    )

  @staticmethod
  def test_connection(engine) -> Tuple[bool, str]:
    try:
      engine.connect()
      return True, "Connection successful"
    except Exception as e:
      return False, str(e)

  @staticmethod
  def upload_dataframe(
    df: pd.DataFrame,
    engine,
    table_name: str,
    if_exists: str = 'replace'
  ) -> Tuple[bool, str]:
    try:
      df.to_sql(table_name, engine, if_exists=if_exists, index=False)
      return True, f"Data successfully uploaded to {table_name}"
    except Exception as e:
      return False, str(e)
