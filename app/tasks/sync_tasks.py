from app.tasks.worker import celery_app


@celery_app.task(name="app.tasks.sync_tasks.poll_google_calendar_changes")
def poll_google_calendar_changes():
    """Poll Google Calendar for changes across all connected users."""
    # Stub — implemented in Phase 1 with full sync logic
    pass


@celery_app.task(name="app.tasks.sync_tasks.sync_blocks_to_google")
def sync_blocks_to_google(user_id: int):
    """Push study blocks to Google Calendar for a specific user."""
    # Stub — implemented in Phase 1
    pass


@celery_app.task(name="app.tasks.sync_tasks.delete_google_events")
def delete_google_events(user_id: int, event_ids: list[str]):
    """Delete Google Calendar events for removed blocks."""
    # Stub — implemented in Phase 1
    pass
