from typing import Optional

from backend.app.persistence.duckdb.service import DuckDbPersistenceService
from backend.app.persistence.minio_storage import MinioService
from app.config.config import SYSTEM_USER_ID, TEAM_NAME, GROUND_TRUTH_AL_INSTANCE_ID, TRAIN_SPLIT, TEST_SPLIT

class StartupService:
    def __init__(
            self, 
            duckdb_service: Optional[DuckDbPersistenceService] = None,
            minio_service: Optional[MinioService] = None
            ):
        self.duckdb_service = duckdb_service
        self.minio_service = minio_service

    def load_data_from_minio_into_duckdb(self):
        # =============== TRAIN TICKETS ===============

        # Fetch the latest timestamp of the train tickets in duckdb
        latest_timestamp_train = self.duckdb_service.get_latest_dataset_timestamp(TRAIN_SPLIT)

        # If there are no tickets, the timestamp will be None, so we have to load all of the tickets
        if latest_timestamp_train is None:
            new_tickets = self.minio_service.load_data(split=TRAIN_SPLIT)
        else:
            # Load the new tickets from MinIO
            new_tickets = self.minio_service.load_data(split=TRAIN_SPLIT,
                                                       latest_dataset_timestamp=latest_timestamp_train
                                                       )

        # If there are new tickets, insert them into duckdb
        if new_tickets is not None and len(new_tickets) > 0:
            for timestamp, tickets_df in new_tickets.items():
                print(f"Loading {len(tickets_df)} new tickets with timestamp {timestamp} into DuckDB...")
                self.duckdb_service.upsert_tickets_df(
                    tickets_df=tickets_df,
                    split=TRAIN_SPLIT,
                    dataset_timestamp=timestamp
                    )
                
        # Some of the tickets might contain ground truth labels (input them into duckdb as well)
        if new_tickets is not None and len(new_tickets) > 0:
            for timestamp, tickets_df in new_tickets.items():
                tickets_df = tickets_df[tickets_df[TEAM_NAME].notna()]
                if len(tickets_df) > 0:
                    print(f"Loading {len(tickets_df)} ground truth ticket labels with timestamp {timestamp} into DuckDB...")
                else:
                    continue
                labels_dict = dict(zip(tickets_df["Ref"], tickets_df[TEAM_NAME]))
                self.duckdb_service.save_labels(
                    al_instance_id=GROUND_TRUTH_AL_INSTANCE_ID,
                    user_id=SYSTEM_USER_ID,  # System user ID for now
                    labels_dict=labels_dict,
                    split=TRAIN_SPLIT,
                    timestamp=timestamp
                    )     

                
        # ===============  TEST TICKETS ===============

        # Fetch the latest timestamp of the test tickets in duckdb
        latest_timestamp_test = self.duckdb_service.get_latest_dataset_timestamp(TEST_SPLIT)

        # If there are no tickets, the timestamp will be None, so we have to load all of the tickets
        if latest_timestamp_test is None:
            new_tickets = self.minio_service.load_data(split=TEST_SPLIT)
        else:
            # Load the new tickets from MinIO
            new_tickets = self.minio_service.load_data(split=TEST_SPLIT,
                                                       latest_dataset_timestamp=latest_timestamp_test
                                                       )

        # We have to make sure that all of the tickets contain the label
        if new_tickets is not None and len(new_tickets) > 0:
            for timestamp, tickets_df in new_tickets.items():
                filtered_df = tickets_df[tickets_df[TEAM_NAME].notna()]
                if len(filtered_df) > 0:
                    new_tickets[timestamp] = filtered_df
                else:
                    del new_tickets[timestamp]

        # If there are new tickets, insert them into duckdb
        if new_tickets is not None and len(new_tickets) > 0:
            for timestamp, tickets_df in new_tickets.items():
                print(f"Loading {len(tickets_df)} new tickets with timestamp {timestamp} into DuckDB...")
                self.duckdb_service.upsert_tickets_df(
                    tickets_df=tickets_df,
                    split=TEST_SPLIT,
                    dataset_timestamp=timestamp
                    )
                
        # Test set also contains the labels. We need to load them into duckdb as well.
        if new_tickets is not None and len(new_tickets) > 0:
            for timestamp, tickets_df in new_tickets.items():
                print(f"Loading labels for {len(tickets_df)} new test tickets with timestamp {timestamp} into DuckDB...")
                labels_dict = dict(zip(tickets_df["Ref"], tickets_df[TEAM_NAME]))
                self.duckdb_service.save_labels(
                    al_instance_id=GROUND_TRUTH_AL_INSTANCE_ID,
                    user_id=SYSTEM_USER_ID,  # System user ID for now
                    labels_dict=labels_dict,
                    split=TEST_SPLIT,
                    timestamp=timestamp
                    )

