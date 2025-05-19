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


class StockView(View):
    template_name = 'data_info.html'

    def get(self, request):
        return render(request, self.template_name, {
            'dados_acao': None,
            'dados_disponiveis': False,
            'erro': None,
            'info_geral': {},
        })

    def post(self, request):
        erro = None
        dados_acao = None
        dados_disponiveis = False
        info_geral = {}
        executivos = []
        media = None
        moda = None 
        mediana = None
        moeda= None
        maior_valor= None
        menor_valor = None
        simbolo = request.POST.get('simbolo')
        periodo = request.POST.get('periodo', '1d')
        translated_summary = 'Não disponível'

        try:
            acao = yf.Ticker(simbolo)
            dados = acao.history(period=periodo)
            info_geral = acao.info

            description = info_geral.get('longBusinessSummary', 'Não disponível')
            translated_summary = GoogleTranslator(source='auto', target='pt').translate(text=description)

            if not dados.empty:
                dados_acao = dados
                dados_disponiveis = True
                media = dados['Close'].mean()  
                moda = dados['Close'].mode()[0]  
                mediana = dados['Close'].median()  
                moeda = info_geral.get('currency', 'Desconhecida')
                maior_valor= dados['Close'].max()
                menor_valor = dados['Close'].min()

                officers = info_geral.get('companyOfficers', [])

                for officer in officers:
                    nome = officer.get('name', 'Não disponível')
                    cargo = officer.get('title', 'Cargo não informado')
                    executivos.append({'nome': nome, 'cargo': cargo})
               

            else:
                erro = "Não foi possível encontrar dados para esse símbolo."

        except Exception as e:
            erro = f"Ocorreu um erro: {str(e)}"
        
      
        info_geral_tratada = {
            'longName': info_geral.get('longName', 'Não disponível'),
            'sector': info_geral.get('sector', 'Não disponível'),
            'industry': info_geral.get('industry', 'Não disponível'),
            'address1': info_geral.get('address1', 'Não disponível'),
            'city': info_geral.get('city', 'Não disponível'),
            'state': info_geral.get('state', 'Não disponível'),
            'website': info_geral.get('website', 'Não disponível'),
            'moeda' : info_geral.get('currency', 'Desconhecida'),
            'fullTimeEmployees': info_geral.get('fullTimeEmployees', 'Não disponível'),
            'longBusinessSummary': translated_summary,
        }

        return render(request, self.template_name, {
            'dados_acao': dados_acao,
            'dados_disponiveis': dados_disponiveis,
            'erro': erro,
            'periodo': periodo,
            'info_geral': info_geral_tratada,
            'executivos': executivos,
            'media': media,
            'moda': moda,
            'mediana': mediana,
            'moeda': moeda,
            'simbolo': simbolo,
            'maior_valor': maior_valor,
            'menor_valor': menor_valor,
        })
