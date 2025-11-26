# from django.shortcuts import render
from .graph import rungraph
#
# from django.http import JsonResponse
# import json
# from django.views.decorators.csrf import csrf_exempt
# from django.http import HttpResponse
#
# def home(request):
#     return render(request, "index.html")
#
# def generate_paper(request):
#     if request.method == "POST":
#         data = json.loads(request.body)
#
#         topic = data.get("topic")
#         field = data.get("field")
#         level = data.get("level")
#         objectives = data.get("objectives")
#         keywords = data.get("keywords")
#
#         user_input = {
#             "topic": topic,
#             "field": field,
#             "level": level,
#             "objectives": objectives,
#             "keywords": keywords
#         }
#
#         # result = rungraph(user_input)
#
#     return render(request, "result.html")
#
#
# def result_page(request):
#     return render(request, "result.html")
from django.shortcuts import render
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt


def home(request):
    """Home page with form"""
    return render(request, "index.html")


@csrf_exempt  # Remove this in production, use proper CSRF
def generate_paper(request):
    """Generate paper endpoint"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            topic = data.get("topic")
            field = data.get("field")
            level = data.get("level")
            objectives = data.get("objectives")
            keywords = data.get("keywords")

            user_input = {
                "topic": topic,
                "field": field,
                "level": level,
                "objectives": objectives,
                "keywords": keywords
            }

            # Uncomment when your graph is ready
            result = rungraph(user_input)
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





        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


def result_page(request):
    """Result page to display generated paper"""
    return render(request, "result.html")