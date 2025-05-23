from django.shortcuts import render
from .templates import *
from django.views.generic import *
from deep_translator import GoogleTranslator
import numpy as np
import pandas as pd
from plotly import plot
import yfinance as yf
import plotly.io as pio
import plotly.graph_objs as go


# Criando Modelos CBV(Class-Based-View)
class HomePage(View):
    def get(self, request, *args, **kwargs):
        tech = yf.Sector('healthcare')
        df = tech.top_companies.head(6).reset_index()
        df.rename(columns={'index': 'symbol'}, inplace=True)

        dados = df.to_dict(orient='records')

        for empresa in dados:
            symbol = empresa['symbol']
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1mo')

            if hist.empty:
                empresa['grafico_html'] = "<p>Sem dados</p>"
                continue

            ymin = min(hist['Open'].min(), hist['Close'].min())
            ymax = max(hist['Open'].max(), hist['Close'].max())

            fig = go.Figure()

            # Linha de Abertura
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['Open'],
                mode='lines+markers',
                name='Abertura',
                line=dict(color='orange'),
                hovertemplate='Data: %{x}<br>Abertura: R$ %{y:.2f}<extra></extra>'
            ))

            # Linha de Fechamento
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['Close'],
                mode='lines+markers',
                name='Fechamento',
                line=dict(color='royalblue'),
                hovertemplate='Data: %{x}<br>Fechamento: R$ %{y:.2f}<extra></extra>'
            ))

            fig.update_layout(
                height=300,
                width=525,
                margin=dict(l=20, r=20, t=30, b=30),
                xaxis_title='Data',
                yaxis_title='Preço',
                template='plotly_white',
                showlegend=True,
                yaxis=dict(
                    range=[ymin * 0.98, ymax * 1.02],  # margem de 2%
                    tickprefix="R$ ",
                    tickformat=".2f"
                )
            )

            empresa['grafico_html'] = pio.to_html(fig, full_html=False, include_plotlyjs=False)

        # Organiza em uma matriz 3x2 (6 elementos -> 3 linhas de 2)
        dados_setores = [dados[i:i + 2] for i in range(0, len(dados), 2)]

        return render(request, 'home.html', {'dados_setores': dados_setores})


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
