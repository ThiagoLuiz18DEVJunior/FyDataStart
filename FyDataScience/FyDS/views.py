from django.shortcuts import render
from .templates import *
from django.views.generic import *
from statsmodels.tsa.ar_model import AutoReg
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.io as pio
import plotly.graph_objs as go
from statsmodels.tsa.stattools import acf
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import acf
from arch import arch_model

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
                translated_summary = info_geral.get('longBusinessSummary', 'Não disponível')


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
            fechamento.index = pd.to_datetime(fechamento.index)
            fechamento = fechamento.asfreq('B')
            fechamento = fechamento.ffill() # IMPORTANTE para evitar NaNs por datas faltantes
            fechamento = fechamento.replace([np.inf, -np.inf], np.nan).dropna()
            


            graficos_por_modelo = {}

            for modelo_nome in modelos_selecionados:
                if modelo_nome == 'AR':
                    fig_linha, fig_acf, fig_hist, fig_scatter = self.rodar_modelo_ar(fechamento, simbolo, periodo)
                elif modelo_nome == 'MA':
                    fig_linha, fig_acf, fig_hist, fig_scatter = self.rodar_modelo_ma(fechamento, simbolo, periodo)
                elif modelo_nome == 'ARMA':
                    fig_linha, fig_acf, fig_hist, fig_scatter = self.rodar_modelo_arma(fechamento, simbolo, periodo)
                elif modelo_nome == 'ARIMA':
                    fig_linha, fig_acf, fig_hist, fig_scatter = self.rodar_modelo_arima(fechamento, simbolo, periodo)
                elif modelo_nome == 'SARIMA':
                    fig_linha, fig_acf, fig_hist, fig_scatter = self.rodar_modelo_sarima(fechamento, simbolo, periodo)
                elif modelo_nome == 'ARCH':
                    fig_linha, fig_acf, fig_hist, fig_scatter = self.rodar_modelo_arch(fechamento, simbolo, periodo)
                elif modelo_nome == 'GARCH':
                    fig_linha, fig_acf, fig_hist, fig_scatter = self.rodar_modelo_garch(fechamento, simbolo, periodo)
                elif modelo_nome == 'Todos':
                     fig_linha, fig_acf, fig_hist, fig_scatter = self.rodar_modelo_ar(fechamento, simbolo, periodo)
                     fig_linha, fig_acf, fig_hist, fig_scatter = self.rodar_modelo_ma(fechamento, simbolo, periodo)
                     fig_linha, fig_acf, fig_hist, fig_scatter = self.rodar_modelo_arma(fechamento, simbolo, periodo)
                     fig_linha, fig_acf, fig_hist, fig_scatter = self.rodar_modelo_arima(fechamento, simbolo, periodo)
                     fig_linha, fig_acf, fig_hist, fig_scatter = self.rodar_modelo_sarima(fechamento, simbolo, periodo)
                     fig_linha, fig_acf, fig_hist, fig_scatter = self.rodar_modelo_arch(fechamento, simbolo, periodo)
                     fig_linha, fig_acf, fig_hist, fig_scatter = self.rodar_modelo_garch(fechamento, simbolo, periodo)
                else:
                    continue

                graficos_por_modelo[modelo_nome] = {
                    'linha': fig_linha.to_html(full_html=False),
                    'acf': fig_acf.to_html(full_html=False),
                    'histograma': fig_hist.to_html(full_html=False),
                    'scatter': fig_scatter.to_html(full_html=False)
                }

            context['graficos_por_modelo'] = graficos_por_modelo

        except Exception as e:
            context['erro'] = str(e)

        return render(request, 'dashboard.html', context)

    # Modelos AR, MA, ARMA, ARIMA, SARIMA - retornam 4 gráficos (linha, acf, histograma, scatter)

    def rodar_modelo_ar(self, fechamento, simbolo, periodo):
        lag = 1
        modelo = AutoReg(fechamento, lags=lag).fit()
        start = lag
        end = len(fechamento) - 1
        previsao = modelo.predict(start=start, end=end, dynamic=False)
        fechamento_slice = fechamento[start:end + 1]

        residuos = fechamento_slice - previsao

        fig_linha, fig_acf = self._criar_graficos(fechamento_slice, previsao, simbolo, periodo, 'AR')
        fig_hist = self.criar_histograma(residuos, 'AR')
        fig_scatter = self.criar_scatter(residuos, 'AR')

        return fig_linha, fig_acf, fig_hist, fig_scatter

    def rodar_modelo_ma(self, fechamento, simbolo, periodo):
        modelo = ARIMA(fechamento, order=(0, 0, 1)).fit()
        start = 1
        end = len(fechamento) - 1
        previsao = modelo.predict(start=start, end=end, dynamic=False)
        fechamento_slice = fechamento[start:end + 1]

        residuos = fechamento_slice - previsao

        fig_linha, fig_acf = self._criar_graficos(fechamento_slice, previsao, simbolo, periodo, 'MA')
        fig_hist = self.criar_histograma(residuos, 'MA')
        fig_scatter = self.criar_scatter(residuos, 'MA')

        return fig_linha, fig_acf, fig_hist, fig_scatter

    def rodar_modelo_arma(self, fechamento, simbolo, periodo):
        modelo = ARIMA(fechamento, order=(1, 0, 1)).fit()
        lag = 1
        start = lag
        end = len(fechamento) - 1
        previsao = modelo.predict(start=start, end=end, dynamic=False)
        fechamento_slice = fechamento[start:end + 1]

        residuos = fechamento_slice - previsao

        fig_linha, fig_acf = self._criar_graficos(fechamento_slice, previsao, simbolo, periodo, 'ARMA')
        fig_hist = self.criar_histograma(residuos, 'ARMA')
        fig_scatter = self.criar_scatter(residuos, 'ARMA')

        return fig_linha, fig_acf, fig_hist, fig_scatter

    def rodar_modelo_arima(self, fechamento, simbolo, periodo):
        modelo = ARIMA(fechamento, order=(1, 1, 1)).fit()
        lag = 1
        start = lag
        end = len(fechamento) - 1
        previsao = modelo.predict(start=start, end=end, dynamic=False)
        fechamento_slice = fechamento[start:end + 1]

        residuos = fechamento_slice - previsao

        fig_linha, fig_acf = self._criar_graficos(fechamento_slice, previsao, simbolo, periodo, 'ARIMA')
        fig_hist = self.criar_histograma(residuos, 'ARIMA')
        fig_scatter = self.criar_scatter(residuos, 'ARIMA')

        return fig_linha, fig_acf, fig_hist, fig_scatter

    def rodar_modelo_sarima(self, fechamento, simbolo, periodo):
        modelo = SARIMAX(fechamento, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12), enforce_stationarity=False, enforce_invertibility=False).fit()
        lag = 1
        start = lag
        end = len(fechamento) - 1
        previsao = modelo.predict(start=start, end=end, dynamic=False)
        fechamento_slice = fechamento[start:end + 1]
        print(modelo.mle_retvals)

        residuos = fechamento_slice - previsao

        fig_linha, fig_acf = self._criar_graficos(fechamento_slice, previsao, simbolo, periodo, 'SARIMA')
        fig_hist = self.criar_histograma(residuos, 'SARIMA')
        fig_scatter = self.criar_scatter(residuos, 'SARIMA')

        return fig_linha, fig_acf, fig_hist, fig_scatter

    def rodar_modelo_arch(self, fechamento, simbolo, periodo):
        am = arch_model(fechamento, vol='ARCH', p=1)
        res = am.fit(disp='off')

        vol_pred = res.conditional_volatility
        std_resid = res.std_resid.dropna()

        fig_linha = go.Figure()
        fig_linha.add_trace(go.Scatter(x=fechamento.index, y=fechamento,
                                      mode='lines', name='Fechamento Real'))
        fig_linha.add_trace(go.Scatter(x=vol_pred.index, y=vol_pred,
                                      mode='lines', name='Volatilidade Condicional (ARCH)', yaxis='y2'))
        fig_linha.update_layout(
            title=f'ARCH - {simbolo} ({periodo})',
            xaxis_title='Data',
            yaxis_title='Preço de Fechamento',
            yaxis2=dict(title='Volatilidade', overlaying='y', side='right'),
            template='ggplot2'
        )

        acf_vals = acf(std_resid, nlags=20)
        fig_acf = go.Figure(go.Bar(x=list(range(len(acf_vals))), y=acf_vals))
        fig_acf.update_layout(title=f'ACF dos resíduos padronizados - ARCH',
                              xaxis_title='Lag', yaxis_title='ACF',
                              template='ggplot2')

        fig_hist = self.criar_histograma(std_resid, 'ARCH')
        fig_scatter = self.criar_scatter(std_resid, 'ARCH')

        return fig_linha, fig_acf, fig_hist, fig_scatter

    def rodar_modelo_garch(self, fechamento, simbolo, periodo):
        am = arch_model(fechamento, vol='Garch', p=1, q=1)
        res = am.fit(disp='off')

        vol_pred = res.conditional_volatility
        std_resid = res.std_resid.dropna()

        fig_linha = go.Figure()
        fig_linha.add_trace(go.Scatter(x=fechamento.index, y=fechamento,
                                      mode='lines', name='Fechamento Real'))
        fig_linha.add_trace(go.Scatter(x=vol_pred.index, y=vol_pred,
                                      mode='lines', name='Volatilidade Condicional (GARCH)', yaxis='y2'))
        fig_linha.update_layout(
            title=f'GARCH - {simbolo} ({periodo})',
            xaxis_title='Data',
            yaxis_title='Preço de Fechamento',
            yaxis2=dict(title='Volatilidade', overlaying='y', side='right'),
            template='ggplot2'
        )

        acf_vals = acf(std_resid, nlags=20)
        fig_acf = go.Figure(go.Bar(x=list(range(len(acf_vals))), y=acf_vals))
        fig_acf.update_layout(title=f'ACF dos resíduos padronizados - GARCH',
                              xaxis_title='Lag', yaxis_title='ACF',
                              template='ggplot2')

        fig_hist = self.criar_histograma(std_resid, 'GARCH')
        fig_scatter = self.criar_scatter(std_resid, 'GARCH')

        return fig_linha, fig_acf, fig_hist, fig_scatter


    def _criar_graficos(self, fechamento_slice, previsao, simbolo, periodo, modelo_nome):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=fechamento_slice.index, y=fechamento_slice,
                                 mode='lines', name='Fechamento Real'))
        fig.add_trace(go.Scatter(x=previsao.index, y=previsao,
                                 mode='lines', name=f'Previsão {modelo_nome}',
                                 line=dict(dash='dot')))

        fig.update_layout(title=f'{modelo_nome} - {simbolo} ({periodo})',
                          xaxis_title='Data',
                          yaxis_title='Preço de Fechamento',
                          template='ggplot2')

        acf_vals = acf(fechamento_slice, nlags=20)
        fig_acf = go.Figure(go.Bar(x=list(range(len(acf_vals))), y=acf_vals))
        fig_acf.update_layout(title=f'Autocorrelação (ACF) - {modelo_nome}',
                              xaxis_title='Lag', yaxis_title='ACF',
                              template='ggplot2')

        return fig, fig_acf

    def criar_histograma(self, residuos, modelo_nome):
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=residuos))
        fig.update_layout(title=f'Histograma dos Resíduos - {modelo_nome}',
                          xaxis_title='Resíduos',
                          yaxis_title='Frequência',
                          template='ggplot2')
        return fig

    def criar_scatter(self, residuos, modelo_nome):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=residuos.index, y=residuos,
                                 mode='markers', name='Resíduos'))
        fig.update_layout(title=f'Gráfico de Dispersão dos Resíduos - {modelo_nome}',
                          xaxis_title='Data',
                          yaxis_title='Resíduos',
                          template='ggplot2')
        return fig
    
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