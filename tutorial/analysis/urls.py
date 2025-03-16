from django.urls import path
from .views import stock_analysis, export_pdf

urlpatterns = [
    path("", stock_analysis, name="stock_analysis"),
    path("export_pdf/", export_pdf, name="export_pdf"),
]
