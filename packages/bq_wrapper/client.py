
from google.cloud import bigquery
from app.core.config import settings

class BigQueryWrapper:

    def __init__(self):
        try:
            self.client = bigquery.Client(project=settings.PROJECT_ID, location=settings.BQ_LOCATION)
        except Exception as e:
            print(f"Warning: BigQuery client could not be initialized (Missing Creds?): {e}")
            self.client = None
        self.dataset_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}"

    def run_query(self, query: str):
        if not self.client:
            raise RuntimeError("BigQuery client is not initialized.")
        query_job = self.client.query(query)
        return query_job.to_dataframe()

bq_client = BigQueryWrapper()
