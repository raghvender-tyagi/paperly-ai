import json
import logging
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from paperlyapp.models import PaperRequest, GeneratedPaper
from paperlyagents.tasks import trigger_paper_generation

logger = logging.getLogger(__name__)


def validate_paper_input(data):
    """Validate and sanitize user input"""
    errors = []
    required_fields = ['topic', 'field', 'level', 'objectives', 'keywords']
    for field in required_fields:
        if not data.get(field):
            errors.append(f"{field} is required")
        elif len(str(data.get(field))) > 500:
            errors.append(f"{field} exceeds maximum length of 500 characters")

    if errors:
        return False, errors
    return True, None


def home(request):
    """Home page with research paper request form"""
    return render(request, "index.html")


@csrf_exempt
def generate_paper(request):
    """Asynchronous submit endpoint for paper generation job"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        is_valid, errors = validate_paper_input(data)
        if not is_valid:
            return JsonResponse({
                "status": "error",
                "message": "Validation failed",
                "errors": errors
            }, status=400)

        # Create PaperRequest record
        paper_req = PaperRequest.objects.create(
            user=request.user if request.user.is_authenticated else None,
            topic=str(data.get("topic"))[:500],
            field=str(data.get("field"))[:100],
            level=str(data.get("level"))[:50],
            objectives=str(data.get("objectives"))[:500],
            keywords=str(data.get("keywords"))[:200],
            status="queued",
            current_section="Queued"
        )

        # Trigger background processing (Celery task with threaded fallback)
        trigger_paper_generation(paper_req.id)

        return JsonResponse({
            "status": "queued",
            "request_id": str(paper_req.id)
        })

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error submitting paper request: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def check_status(request, request_id):
    """Poll endpoint to check background task status and current section"""
    paper_req = get_object_or_404(PaperRequest, id=request_id)
    return JsonResponse({
        "status": paper_req.status,
        "current_section": paper_req.current_section,
        "error": paper_req.error_message
    })


def get_result_api(request, request_id):
    """API endpoint to retrieve full paper details in JSON"""
    paper_req = get_object_or_404(PaperRequest, id=request_id)

    if paper_req.status != "done":
        return JsonResponse({
            "status": paper_req.status,
            "message": f"Paper is not complete yet (current status: {paper_req.status})"
        }, status=400)

    try:
        gen_paper = paper_req.generated_paper
        title = gen_paper.title
        novelty = gen_paper.novelty
    except GeneratedPaper.DoesNotExist:
        title = paper_req.topic
        novelty = ""

    sections = {sec.section_type: sec.content for sec in paper_req.sections.all()}

    output = {
        "id": str(paper_req.id),
        "title": title,
        "topic": paper_req.topic,
        "field": paper_req.field,
        "level": paper_req.level,
        "keywords": paper_req.keywords,
        "novelty": novelty,
        "abstract": sections.get("abstract", ""),
        "introduction": sections.get("introduction", ""),
        "literature_review": sections.get("literature_review", ""),
        "methodology": sections.get("methodology", ""),
        "conclusion": sections.get("conclusion", "")
    }

    return JsonResponse({"status": "success", "output": output})


def result_page(request, request_id=None):
    """Render result HTML page for a specific paper request"""
    context = {"request_id": request_id}
    return render(request, "result.html", context)
