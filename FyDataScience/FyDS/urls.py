from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('', HomePage.as_view(), name='Home'),
    path('Stock', StockView.as_view(), name='Stock' )
    
]
