from django.shortcuts import render
from .templates import *

def home(request):
    return render(request, 'base.html')


