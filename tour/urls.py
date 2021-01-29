from django.conf.urls import url
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('move_forward/',views.move),
    path('q1/', views.q1),
    path('q2/', views.q2),
    path('result/',views.result),
    path('loading/',views.loading)
]