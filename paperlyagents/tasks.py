import threading
from django.utils import timezone
from celery import shared_task
from paperlyapp.models import PaperRequest, PaperSection, GeneratedPaper
from paperlyagents.graph import rungraph


def process_paper_request(paper_request_id):
    """Execute paper generation pipeline and persist results to DB."""
    try:
        paper_req = PaperRequest.objects.get(id=paper_request_id)
    except PaperRequest.DoesNotExist:
        print(f"PaperRequest {paper_request_id} not found.")
        return

    paper_req.status = "running"
    paper_req.current_section = "Initializing..."
    paper_req.save()

    def update_progress(section):
        paper_req.current_section = section
        paper_req.save(update_fields=['current_section'])

    try:
        user_input = {
            "topic": paper_req.topic,
            "field": paper_req.field,
            "level": paper_req.level,
            "objectives": paper_req.objectives,
            "keywords": paper_req.keywords,
        }

        result = rungraph(user_input, progress_callback=update_progress)

        # Save sections into DB
        sections_map = [
            ("introduction", result.get("introduction", "")),
            ("literature_review", result.get("literature_review", "")),
            ("methodology", result.get("methodology", "")),
            ("conclusion", result.get("conclusion", "")),
            ("abstract", result.get("abstract", "")),
        ]

        for section_type, content in sections_map:
            PaperSection.objects.create(
                paper=paper_req,
                section_type=section_type,
                content=content
            )

        # Save GeneratedPaper model
        GeneratedPaper.objects.update_or_create(
            request=paper_req,
            defaults={
                "title": result.get("title", paper_req.topic),
                "novelty": result.get("novelty", "")
            }
        )

        paper_req.status = "done"
        paper_req.current_section = "Completed"
        paper_req.completed_at = timezone.now()
        paper_req.save()

    except Exception as e:
        paper_req.status = "failed"
        paper_req.error_message = str(e)
        paper_req.save()
        print(f"Error executing paper generation task: {e}")


@shared_task(bind=True, max_retries=2)
def generate_paper_task(self, paper_request_id):
    """Celery background task."""
    process_paper_request(paper_request_id)


def trigger_paper_generation(paper_request_id):
    """Trigger generation via Celery if available, or fall back to threaded background worker."""
    try:
        generate_paper_task.delay(str(paper_request_id))
    except Exception as e:
        print(f"Celery dispatch failed ({e}), falling back to background thread.")
        thread = threading.Thread(target=process_paper_request, args=(paper_request_id,))
        thread.daemon = True
        thread.start()
