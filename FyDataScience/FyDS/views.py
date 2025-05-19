from django.shortcuts import render
from .templates import *
from django.views.generic import *
from deep_translator import GoogleTranslator
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go


# Criando Modelos CBV(Class-Based-View)

class HomePage(TemplateView):
    template_name = 'base.html'


def buscar_acao(request):
    erro = None
    dados_acao = None
    dados_disponiveis = False
    info_geral = {}

    if request.method == 'POST':
        simbolo = request.POST.get('simbolo')
        try:
            acao = yf.Ticker(simbolo)
            dados = acao.history(period='1d')
            info_geral = acao.info  # Obter as informações gerais
            long_business_summary = info_geral.get('longBusinessSummary', 'Não disponível')
            translated_summary = GoogleTranslator(source='auto', target='pt').translate(text=long_business_summary)

            if not dados.empty:
                dados_acao = dados
                dados_disponiveis = True
            else:
                erro = "Não foi possível encontrar dados para esse símbolo."
        except Exception as e:
            erro = f"Ocorreu um erro: {str(e)}"

    # Preprocessa as informações gerais
    info_geral_tratada = {
        'longName': info_geral.get('longName', 'Não disponível'),
        'sector': info_geral.get('sector', 'Não disponível'),
        'industry': info_geral.get('industry', 'Não disponível'),
        'ceo': info_geral.get('ceo', 'Não disponível'),
        'address1': info_geral.get('address1', 'Não disponível'),
        'city': info_geral.get('city', 'Não disponível'),
        'state': info_geral.get('state', 'Não disponível'),
        'website': info_geral.get('website', 'Não disponível'),
        'longBusinessSummary': translated_summary,
    }



    return render(request, 'data_info.html', {
        'dados_acao': dados_acao,
        'dados_disponiveis': dados_disponiveis,
        'erro': erro,
        'info_geral': info_geral_tratada,
    })
