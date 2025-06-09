from django.shortcuts import render
from .templates import *
from django.views.generic import *
from deep_translator import GoogleTranslator
from statsmodels.tsa.ar_model import AutoReg
import numpy as np
import pandas as pd
from scipy.stats import linregress
from plotly import plot
import yfinance as yf
import plotly.io as pio
import plotly.graph_objs as go
from scipy.stats import pearsonr
from statsmodels.tsa.stattools import acf
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import acf
from scipy.stats import pearsonr, shapiro

# Criando Modelos CBV(Class-Based-View)
class HomePage(View):
    def get(self, request, *args, **kwargs):
        setor = request.GET.get('setor', 'technology')
        periodo = request.GET.get('periodo', '1wk')
        moeda = request.GET.get('moeda', 'US$')
        dados = []
        dados_setores = []

        try:
            sector_data = yf.Sector(setor)
            df = sector_data.top_companies

            if isinstance(df, pd.DataFrame) and not df.empty:
                df = df.head(6)
                df = df.reset_index()
                if 'index' in df.columns:
                    df.rename(columns={'index': 'symbol'}, inplace=True)

                dados = df.to_dict(orient='records')

                for empresa in dados:
                    symbol = empresa.get('symbol')
                    if not symbol:
                        continue

                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period=periodo)

                    if hist.empty:
                        empresa['grafico_html'] = "<p>Sem dados</p>"
                        continue

                    ymin = min(hist['Open'].min(), hist['Close'].min())
                    ymax = max(hist['Open'].max(), hist['Close'].max())

                    fig = go.Figure()

                    fig.add_trace(go.Scatter(
                        x=hist.index,
                        y=hist['Open'],
                        mode='lines+markers',
                        name='Abertura',
                        line=dict(color='orange'),
                        hovertemplate=f'Data: %{{x}}<br>Abertura: {"R$" if moeda == "BRL" else "US$"} %{{y:.2f}}<extra></extra>'
                    ))

                    fig.add_trace(go.Scatter(
                        x=hist.index,
                        y=hist['Close'],
                        mode='lines+markers',
                        name='Fechamento',
                        line=dict(color='royalblue'),
                        hovertemplate=f'Data: %{{x}}<br>Fechamento: {"R$" if moeda == "BRL" else "US$"} %{{y:.2f}}<extra></extra>'
                    ))

                    fig.update_layout(
                        height=300,
                        width=500,
                        margin=dict(l=20, r=20, t=30, b=30),
                        xaxis_title='Data',
                        yaxis_title='Preço',
                        template='plotly_white',
                        showlegend=True,
                        yaxis=dict(
                            range=[ymin * 0.98, ymax * 1.02],
                            tickprefix="R$ " if moeda == "BRL" else "US$ ",
                            tickformat=".2f"
                        )
                    )

                    empresa['grafico_html'] = pio.to_html(fig, full_html=False, include_plotlyjs=False)
            else:
                dados = []

        except Exception as e:
            print(f"[ERRO] Falha ao carregar setor '{setor}': {e}")
            dados = []

        dados_setores = [dados[i:i + 2] for i in range(0, len(dados), 2)]

        contexto = {
            'dados_setores': dados_setores,
            'setor_selecionado': setor,
            'periodo_selecionado': periodo,
            'moeda_selecionada': moeda,
        }

        return render(request, 'home.html', contexto)

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

class DashView(View):
    def get(self, request):
        return render(request, 'dashboard.html')

    def post(self, request):
        simbolo = request.POST.get('simbolo')
        periodo = request.POST.get('periodo')
        modelos_selecionados = request.POST.getlist('modelos')  

        context = {}

        try:
            dados = yf.Ticker(simbolo).history(period=periodo)
            if dados.empty:
                raise ValueError("Nenhum dado encontrado para o símbolo informado.")

            fechamento = dados['Close']

            graficos = []
            graficos_acf = []

            for modelo_nome in modelos_selecionados:
                if modelo_nome == 'AR':
                    fig, fig_acf = self.rodar_modelo_ar(fechamento, simbolo, periodo)
                elif modelo_nome == 'MA':
                    fig, fig_acf = self.rodar_modelo_ma(fechamento, simbolo, periodo)
                elif modelo_nome == 'ARMA':
                    fig, fig_acf = self.rodar_modelo_arma(fechamento, simbolo, periodo)
                elif modelo_nome == 'ARIMA':
                    fig, fig_acf = self.rodar_modelo_arima(fechamento, simbolo, periodo)
                elif modelo_nome == 'SARIMA':
                    fig, fig_acf = self.rodar_modelo_sarima(fechamento, simbolo, periodo)
                else:
                    continue

                graficos.append(fig.to_html(full_html=False))
                graficos_acf.append(fig_acf.to_html(full_html=False))

            context['graficos'] = graficos
            context['graficos_acf'] = graficos_acf

        except Exception as e:
            context['erro'] = str(e)

        return render(request, 'dashboard.html', context)

    # Exemplo do método rodar_modelo_ar:
    def rodar_modelo_ar(self, fechamento, simbolo, periodo):
        lag = 6
        modelo = AutoReg(fechamento, lags=lag).fit()
        start = lag
        end = len(fechamento) - 1
        previsao = modelo.predict(start=start, end=end, dynamic=False)
        fechamento_slice = fechamento[start:end + 1]
        

        # Gráfico (exemplo simplificado)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=fechamento_slice.index, y=fechamento_slice, mode='lines', name='Fechamento Real'))
        fig.add_trace(go.Scatter(x=previsao.index, y=previsao, mode='lines', name='Previsão AR'))

        fig.update_layout(title=f'AR - {simbolo} ({periodo})', xaxis_title='Data', yaxis_title='Preço')

        # ACF
        acf_vals = acf(fechamento, nlags=20)
        fig_acf = go.Figure(go.Bar(x=list(range(len(acf_vals))), y=acf_vals))
        fig_acf.update_layout(title='Autocorrelação (ACF)', xaxis_title='Lag', yaxis_title='ACF')

        return fig, fig_acf

    def rodar_modelo_ma(self, fechamento, simbolo, periodo):
        # MA(1) como exemplo, ordem (0,0,1)
        modelo = ARIMA(fechamento, order=(0, 0, 1)).fit()
        start = 1  # para MA(1), a previsão começa do índice 1
        end = len(fechamento) - 1
        previsao = modelo.predict(start=start, end=end, dynamic=False)
        fechamento_slice = fechamento[start:end + 1]

        return self._criar_graficos(fechamento_slice, previsao, simbolo, periodo, 'MA')

    def rodar_modelo_arma(self, fechamento, simbolo, periodo):
        # ARMA(1,1) exemplo, ordem (1,0,1)
        modelo = ARIMA(fechamento, order=(1, 0, 1)).fit()
        lag = max(1, 1)  # maior entre AR e MA lag
        start = lag
        end = len(fechamento) - 1
        previsao = modelo.predict(start=start, end=end, dynamic=False)
        fechamento_slice = fechamento[start:end + 1]

        return self._criar_graficos(fechamento_slice, previsao, simbolo, periodo, 'ARMA')

    def rodar_modelo_arima(self, fechamento, simbolo, periodo):
        # ARIMA(1,1,1) exemplo — 1 diferença para estacionarizar
        modelo = ARIMA(fechamento, order=(1, 1, 1)).fit()
        lag = 1  # AR lag
        start = lag
        end = len(fechamento) - 1
        previsao = modelo.predict(start=start, end=end, dynamic=False)
        fechamento_slice = fechamento[start:end + 1]

        return self._criar_graficos(fechamento_slice, previsao, simbolo, periodo, 'ARIMA')

    def rodar_modelo_sarima(self, fechamento, simbolo, periodo):
        # SARIMA(1,1,1)(1,1,1,12) exemplo com sazonalidade 12
        modelo = SARIMAX(fechamento, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12)).fit()
        lag = 1  # considerar o AR lag
        start = lag
        end = len(fechamento) - 1
        previsao = modelo.predict(start=start, end=end, dynamic=False)
        fechamento_slice = fechamento[start:end + 1]

        return self._criar_graficos(fechamento_slice, previsao, simbolo, periodo, 'SARIMA')

    def _criar_graficos(self, fechamento_slice, previsao, simbolo, periodo, modelo_nome):
        # Gráfico dos valores reais e previstos
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=fechamento_slice.index, y=fechamento_slice,
                                 mode='lines', name='Fechamento Real'))
        fig.add_trace(go.Scatter(x=previsao.index, y=previsao,
                                 mode='lines', name=f'Previsão {modelo_nome}', line=dict(dash='dot')))

        fig.update_layout(title=f'{modelo_nome} - {simbolo} ({periodo})',
                          xaxis_title='Data',
                          yaxis_title='Preço de Fechamento',
                          template='plotly_white')

        # Gráfico de ACF
        acf_vals = acf(fechamento_slice, nlags=20)
        fig_acf = go.Figure(go.Bar(x=list(range(len(acf_vals))), y=acf_vals))
        fig_acf.update_layout(title=f'Autocorrelação (ACF) - {modelo_nome}',
                              xaxis_title='Lag',
                              yaxis_title='ACF',
                              template='plotly_white')

        return fig, fig_acf
class InfoView(View):
    def get(self, request, *args, **kwargs):
        # Lógica para InfoView
        return render(request, 'info.html')

class DocView(View):
    def get(self, request, *args, **kwargs):
        # Lógica para DocView
        return render(request, 'document.html')

class DevsView(View):
    def get(self, request, *args, **kwargs):
        # Lógica para DevsView
        return render(request, 'dev.html')