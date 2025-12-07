from django.shortcuts import render
from django.http import JsonResponse
import json
import logging

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
    """Home page with form"""
    return render(request, "index.html")


def generate_paper(request):
    """Generate paper endpoint"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            
            # Validate input
            is_valid, errors = validate_paper_input(data)
            if not is_valid:
                return JsonResponse({
                    "status": "error",
                    "message": "Validation failed",
                    "errors": errors
                }, status=400)
            
            # Sanitize and extract with length limits
            user_input = {
                "topic": str(data.get("topic"))[:500],
                "field": str(data.get("field"))[:100],
                "level": str(data.get("level"))[:50],
                "objectives": str(data.get("objectives"))[:500],
                "keywords": str(data.get("keywords"))[:200]
            }

            # Run the graph
            from .graph import rungraph
            try:
                result = rungraph(user_input)
            except Exception as e:
                import traceback
                from django.conf import settings
                
                logger.error(f"ERROR in rungraph: {str(e)}")
                logger.error(traceback.format_exc())
                
                # Don't expose details in production
                error_msg = str(e) if settings.DEBUG else "An error occurred processing your request"
                return JsonResponse({
                    "status": "error",
                    "message": error_msg
                }, status=500)
            
            clean_output = {
                "title": result.get("title", ""),
                "abstract": result.get("abstract", ""),
                "introduction": result.get("introduction", ""),
                "literature_review": result.get("literature_review", ""),
                "methodology": result.get("methodology", ""),
                "conclusion": result.get("conclusion", ""),
                "keywords": user_input.get("keywords", "")
            }

            return JsonResponse({"status": "success", "output": clean_output})

        except json.JSONDecodeError:
            return JsonResponse({
                "status": "error",
                "message": "Invalid JSON"
            }, status=400)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JsonResponse({
                "status": "error",
                "message": "An unexpected error occurred"
            }, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)


def result_page(request):
    """Result page to display generated paper"""
    return render(request, "result.html")
