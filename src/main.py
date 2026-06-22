import sys
from datetime import datetime
from metadata_reader import load_metadata
from pipeline_executor import run_pipeline
from audit_logger import log_audit

def main():
   # =================================================
   # STEP 1 → GET PIPELINE ID
   # =================================================
   if len(sys.argv) < 2:
       print(
           "Usage: python main.py <pipeline_id>"
       )
       return
   pipeline_id = sys.argv[1]
   # =================================================
   # STEP 2 → LOAD METADATA
   # =================================================
   metadata_df = load_metadata(
       pipeline_id
   )
   if metadata_df.empty:
       print(
           f"No pipeline found for "
           f"pipeline_id = {pipeline_id}"
       )
       return
   # =================================================
   # STEP 3 → RUN PIPELINE
   # =================================================
   for _, row in metadata_df.iterrows():
       start_time = datetime.now()
       print(
           f"\nRunning pipeline: "
           f"{row['pipeline_name']} "
           f"({row['pipeline_mode']})"
       )
       try:
           result = run_pipeline(row)
           # =========================================
           # ROW COUNT CALCULATION
           # =========================================
           if isinstance(result, int):
               records_processed = result
           elif hasattr(result, "__len__"):
               records_processed = len(result)
           else:
               records_processed = 0
           print(
               f"Completed: "
               f"{records_processed} rows processed"
           )
           end_time = datetime.now()
           duration_seconds = (
               end_time - start_time
           ).total_seconds()
           # =========================================
           # AUDIT SUCCESS
           # =========================================
           log_audit(
               pipeline_id=row["pipeline_id"],
               pipeline_name=row["pipeline_name"],
               start_time=start_time,
               end_time=end_time,
               status="SUCCESS",
               records_processed=records_processed,
               duration_seconds=duration_seconds,
               error_message=None
           )
       except Exception as e:
           end_time = datetime.now()
           duration_seconds = (
               end_time - start_time
           ).total_seconds()
           # =========================================
           # AUDIT FAILURE
           # =========================================
           log_audit(
               pipeline_id=row["pipeline_id"],
               pipeline_name=row["pipeline_name"],
               start_time=start_time,
               end_time=end_time,
               status="FAILED",
               records_processed=0,
               duration_seconds=duration_seconds,
               error_message=str(e)
           )
           print(
               f"❌ Failed: {e}"
           )
           raise

if __name__ == "__main__":
   main()