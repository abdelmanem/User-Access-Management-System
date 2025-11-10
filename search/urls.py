from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.global_search, name='global_search'),
    path('suggestions/', views.search_suggestions, name='search_suggestions'),
    path('advanced/', views.advanced_search, name='advanced_search'),
]