from django.urls import path
from paperlyapp.views import home, generate_paper, check_status, get_result_api, result_page

urlpatterns = [
    path("", home, name="index"),
    path("generate/", generate_paper, name="generate_paper"),
    path("status/<uuid:request_id>/", check_status, name="check_status"),
    path("api/result/<uuid:request_id>/", get_result_api, name="get_result_api"),
    path("result/", result_page, name="result_page"),
    path("result/<uuid:request_id>/", result_page, name="result_page_with_id"),
]