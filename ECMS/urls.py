from django.urls import path
from . import views

app_name = "ECMS"

urlpatterns = [
    path('', views.campaign_list, name='campaign_list'),
    path('campaign/create/', views.campaign_create, name='campaign_create'),
    path('campaign/<int:pk>/', views.campaign_detail, name='campaign_detail'),
    path('recipients/upload/', views.upload_recipients, name='upload_recipients'),
    path('campaign/<int:pk>/send/', views.send_campaign, name='send_campaign'),
]
