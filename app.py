"""Meus treinos — app Streamlit. Rodar com: streamlit run app.py"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from config import COLUNAS_ZONAS, PERIODOS
from dados import agrupar_zonas, carregar
from graficos import distribuicao, historico

CSV_PADRAO = Path(__file__).with_name('workouts.csv')

# Colunas internas criadas em dados.py; ficam fora do CSV exportado.
COLUNAS_DERIVADAS = {'data', 'exercicio', 'duracao_s', 'distancia_km',
                     'zonas_n', 'zonas_s', 'tem_zonas', 'periodo', *COLUNAS_ZONAS}

COLUNAS_TABELA = {  # coluna do CSV -> título exibido
    'Date': 'Data', 'Time': 'Hora', 'exercicio': 'Exercício', 'Total Time': 'Duração',
    'Distance': 'Distância', 'Avg. Heart Rate': 'FC média', 'TRIMP': 'TRIMP', 'RPE': 'RPE',
    'periodo': 'Período do dispositivo', 'tem_zonas': 'Zonas disponíveis',
}


@st.cache_data
def ler(conteudo):
    return carregar(conteudo)


# ---------- carregamento ----------

def carregar_dados():
    """Lê o CSV enviado (ou o padrão). Para a execução se não for possível."""
    arquivo = st.sidebar.file_uploader('Carregar outra exportação', type=['csv'])
    try:
        conteudo = arquivo.getvalue() if arquivo else CSV_PADRAO.read_bytes()
        dados, avisos = ler(conteudo)
    except (ValueError, UnicodeError, OSError, pd.errors.ParserError) as e:
        st.error(f'Não foi possível carregar o CSV: {e}')
        st.stop()
    if dados.empty:
        st.info('O arquivo não tem atividades com datas válidas.')
        st.stop()
    return dados, avisos


# ---------- filtros ----------

def sidebar_filtros(dados):
    """Desenha os filtros na barra lateral e devolve (exercicios, periodos, datas)."""
    st.sidebar.header('Filtros')

    opcoes = sorted(dados['exercicio'].unique())
    corridas = [e for e in opcoes if e.startswith('Corrida')]
    exercicios = st.sidebar.multiselect('Exercícios', opcoes, default=corridas or opcoes)

    data_min, data_max = dados['data'].min().date(), dados['data'].max().date()
    # inicio_padrao = max(data_min, (pd.Timestamp(data_max) - pd.Timedelta(days=89)).date())  # últimos 90 dias
    inicio_padrao = '2026-01-01'
    datas = st.sidebar.date_input('Período', value=(inicio_padrao, data_max),
                                  min_value=data_min, max_value=data_max, format='YYYY-MM-DD')

    periodos = st.sidebar.multiselect('Período do dispositivo', PERIODOS, default=PERIODOS[-1])
    st.sidebar.caption('Classificação pelas datas informadas: Mi Band desde 05/11/2019; '
                       'AW 3 desde 11/03/2020; AW 11 desde 21/03/2026. '
                       'Não identifica a origem de cada treino.')
    return exercicios, periodos, datas


def filtrar(dados, exercicios, periodos, datas):
    inicio, fim = pd.Timestamp(datas[0]), pd.Timestamp(datas[1])
    mascara = (dados['exercicio'].isin(exercicios)
               & dados['periodo'].isin(periodos)
               & dados['data'].between(inicio, fim))
    return dados.loc[mascara].copy()


# ---------- seções da página ----------

def secao_resumo(d, avisos):
    if any(avisos.values()):
        st.caption(f"Na importação: {avisos['duplicados']} UUIDs repetidos removidos; "
                   f"{avisos['datas_invalidas']} datas inválidas ignoradas.")

    c1, c2, c3 = st.columns(3)
    c1.metric('Atividades', len(d))
    c2.metric('Tempo total', f"{d['duracao_s'].sum() / 3600:.1f} h")
    tem_distancia = d['distancia_km'].notna().any()
    c3.metric('Distância registrada', f"{d['distancia_km'].sum():.2f} km" if tem_distancia else '—')
    st.caption(f"Duração disponível em {d['duracao_s'].notna().sum()} de {len(d)} atividades; "
               f"distância em {d['distancia_km'].notna().sum()}. "
               'Distância soma apenas os registros disponíveis.')


def secao_distribuicao(totais):
    modo = st.radio('Exibir distribuição em', ['Horas', 'Percentual'], horizontal=True)
    fig = distribuicao(totais, modo == 'Percentual')
    st.pyplot(fig)
    plt.close(fig)
    st.caption('Percentuais calculados sobre a soma do tempo registrado nas zonas, '
               'ponderados pela duração. Essa soma pode diferir do tempo total da atividade.')


def secao_historico(d):
    st.subheader('Zonas ao longo do tempo')
    c1, c2 = st.columns(2)
    grupo = c1.selectbox('Agrupar por', ['Treino', 'Semana', 'Mês'], index=1)
    unidade = c2.radio('Exibir histórico em', ['Minutos', 'Percentual'], horizontal=True)

    tabela = agrupar_zonas(d, grupo)
    if grupo == 'Treino' and len(tabela) > 150:
        st.caption('Muitos treinos neste recorte. O agrupamento por semana ou mês facilita a leitura.')
    fig = historico(tabela, unidade == 'Percentual')
    st.pyplot(fig)
    plt.close(fig)
    st.caption('Semanas começam na segunda-feira. Espaços sem barras indicam ausência de tempo de zonas '
               'disponível; não comprovam ausência de exercício. Os períodos nas bordas podem estar incompletos.')


def secao_valores_zonas(totais):
    with st.expander('Ver valores das zonas'):
        resumo = pd.DataFrame({
            'Zona': [f'Z{i}' for i in range(1, 6)],
            'Minutos': totais.to_numpy() / 60,
            'Percentual': totais.to_numpy() / totais.sum() * 100,
        })
        st.dataframe(resumo.round(2), hide_index=True, width='stretch')


def secao_zonas(d):
    st.subheader('Distribuição nas zonas')
    z = d.loc[d['tem_zonas']]
    st.caption(f'Zonas HRR disponíveis em {len(z)} de {len(d)} atividades selecionadas. '
               'Registros sem informação de zonas ficam fora destes gráficos.')
    if z.empty:
        st.info('Não há registros HRR de cinco zonas com tempo positivo neste recorte.')
        return
    totais = z[COLUNAS_ZONAS].sum()
    secao_distribuicao(totais)
    secao_historico(d)
    secao_valores_zonas(totais)


def secao_tabela(d):
    st.subheader('Atividades selecionadas')
    colunas = [c for c in COLUNAS_TABELA if c in d]
    tabela = d.sort_values(['data', 'Time'], ascending=False)[colunas].rename(columns=COLUNAS_TABELA)
    st.dataframe(tabela, hide_index=True, width='stretch')

    originais = [c for c in d if c not in COLUNAS_DERIVADAS]
    csv = d[originais].to_csv(index=False, sep=';').encode('utf-8-sig')
    st.download_button('Baixar atividades filtradas (CSV)', csv,
                       file_name='treinos_filtrados.csv', mime='text/csv')


# ---------- página ----------

def main():
    st.set_page_config(page_title='Meus treinos', page_icon='🏃', layout='wide')
    st.title('Meus treinos')
    st.caption('Explore suas atividades e o tempo registrado nas zonas cardíacas.')

    dados, avisos = carregar_dados()
    exercicios, periodos, datas = sidebar_filtros(dados)
    if len(datas) != 2:
        st.info('Selecione a data inicial e a final.')
        st.stop()

    d = filtrar(dados, exercicios, periodos, datas)
    if d.empty:
        st.info('Nenhuma atividade corresponde aos filtros. '
                'Experimente ampliar o período ou selecionar outros exercícios.')
        st.stop()

    secao_resumo(d, avisos)
    secao_zonas(d)
    secao_tabela(d)


main()

