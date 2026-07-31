import json
from typing import Dict, Any
from backend.core.celery_app import celery_app
from backend.core.config import settings
from backend.core.logger import logger
from database.postgres import SessionLocal
from backend.models.schema import AuditLog

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


@celery_app.task(name="audit.tasks.archive_trace_to_s3", bind=True, max_retries=3)
def archive_trace_to_s3(self, trace_dict: Dict[str, Any]) -> str:
    """
    Celery task to archive the immutable JSONL trace payload to AWS S3.
    """
    run_id = trace_dict.get("run_id", "unknown_run")
    if not settings.ENABLE_S3_ARCHIVAL or not BOTO3_AVAILABLE:
        logger.info(
            "S3 archival disabled or boto3 unavailable. Skipping S3 upload",
            run_id=run_id
        )
        return "S3_ARCHIVAL_SKIPPED"

    try:
        s3 = boto3.client("s3", region_name=settings.AWS_REGION)
        jsonl_content = json.dumps(trace_dict, ensure_ascii=False) + "\n"
        object_key = f"traces/{trace_dict.get('session_id', 'unknown_session')}/{run_id}.jsonl"

        s3.put_object(
            Bucket=settings.S3_AUDIT_BUCKET_NAME,
            Key=object_key,
            Body=jsonl_content.encode("utf-8"),
            ContentType="application/x-ndjson",
            ServerSideEncryption="AES256"
        )
        logger.info("Trace successfully archived to AWS S3", run_id=run_id, object_key=object_key)
        return f"s3://{settings.S3_AUDIT_BUCKET_NAME}/{object_key}"
    except Exception as exc:
        logger.error("Failed to archive trace to S3, retrying...", run_id=run_id, error=str(exc))
        raise self.retry(exc=exc, countdown=10)


@celery_app.task(name="audit.tasks.async_persist_audit_log")
def async_persist_audit_log(
    correlation_id: str,
    event_type: str,
    actor_id: str,
    entity_type: str,
    entity_id: str,
    action_details: str
) -> bool:
    """
    Celery background worker task for high-throughput asynchronous audit log insertions.
    """
    db = SessionLocal()
    try:
        log_entry = AuditLog(
            correlation_id=correlation_id,
            event_type=event_type,
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action_details=action_details
        )
        db.add(log_entry)
        db.commit()
        return True
    except Exception as exc:
        logger.error("Failed to persist async audit log entry", error=str(exc))
        return False
    finally:
        db.close()
