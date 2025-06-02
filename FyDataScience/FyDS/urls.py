from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('', HomePage.as_view(), name='Home'),
    path('Stock', StockView.as_view(), name='Stock'),
    path('Dash', DashView.as_view(), name='Dash'),
    path('NerdEst', NerdView.as_view(), name='Nerd'),
    path('Info', InfoView.as_view(), name='Info'),
    path('Doc', DocView.as_view(), name='Doc'),
    path('Dev', DevsView.as_view(), name='Dev')
]
