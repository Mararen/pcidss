from django.urls import path
from . import views

app_name = 'helpdesk'

urlpatterns = [
    path('', views.ticket_lista, name='ticket_lista'),
    path('nuevo/', views.ticket_nuevo, name='ticket_nuevo'),
    path('<int:pk>/', views.ticket_detalle, name='ticket_detalle'),
    path('<int:pk>/comentario/', views.agregar_comentario, name='agregar_comentario'),
    path('<int:pk>/cambiar_estado/', views.cambiar_estado, name='cambiar_estado'),
]