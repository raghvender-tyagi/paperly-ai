from django.urls import path
from .views import home
from .views import generate_paper
from .views import result_page

urlpatterns = [
    path("", home, name="index"),
    path("generate/", generate_paper, name="generate_paper"),
    path("result/", result_page, name="result_page"),
]