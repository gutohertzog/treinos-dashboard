from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from dados import carregar, agrupar_zonas, PERIODOS
from graficos import distribuicao, historico

st.set_page_config(page_title='Meus treinos', page_icon='🏃', layout='wide')
st.title('Meus treinos')
st.caption('Explore suas atividades e o tempo registrado nas zonas cardíacas.')

@st.cache_data
def ler(conteudo): return carregar(conteudo)

arquivo = st.sidebar.file_uploader('Carregar outra exportação', type=['csv'])
try:
    conteudo = arquivo.getvalue() if arquivo else Path(__file__).with_name('workouts.csv').read_bytes()
    dados, avisos = ler(conteudo)
except (ValueError, UnicodeError, OSError, pd.errors.ParserError) as e:
    st.error(f'Não foi possível carregar o CSV: {e}')
    st.stop()
if dados.empty:
    st.info('O arquivo não tem atividades com datas válidas.')
    st.stop()

st.sidebar.header('Filtros')
escolhas = sorted(dados['exercicio'].unique())
iniciais = [e for e in escolhas if e.startswith('Corrida')]
exercicios = st.sidebar.multiselect('Exercícios', escolhas, default=iniciais or escolhas)
limite = dados['data'].max().date()
inicio = max(dados['data'].min().date(), (pd.Timestamp(limite) - pd.Timedelta(days=89)).date())
datas = st.sidebar.date_input('Período', value=(inicio, limite), min_value=dados['data'].min().date(), max_value=limite, format='DD/MM/YYYY')
periodos = st.sidebar.multiselect('Período do dispositivo', PERIODOS, default=PERIODOS)
st.sidebar.caption('Classificação pelas datas informadas: Mi Band desde 05/11/2019; AW 3 desde 11/03/2020; AW 11 desde 21/03/2026. Não identifica a origem de cada treino.')
if len(datas) != 2:
    st.info('Selecione a data inicial e a final.')
    st.stop()
d = dados.loc[dados['exercicio'].isin(exercicios) & dados['periodo'].isin(periodos)
              & dados['data'].between(pd.Timestamp(datas[0]), pd.Timestamp(datas[1]))].copy()
if d.empty:
    st.info('Nenhuma atividade corresponde aos filtros. Experimente ampliar o período ou selecionar outros exercícios.')
    st.stop()
if any(avisos.values()): st.caption(f"Na importação: {avisos['duplicados']} UUIDs repetidos removidos; {avisos['datas_invalidas']} datas inválidas ignoradas.")

c1, c2, c3 = st.columns(3)
c1.metric('Atividades', len(d))
c2.metric('Tempo total', f"{d['duracao_s'].sum()/3600:.1f} h")
c3.metric('Distância registrada', f"{d['distancia_km'].sum():.2f} km" if d['distancia_km'].notna().any() else '—')
st.caption(f"Duração disponível em {d['duracao_s'].notna().sum()} de {len(d)} atividades; distância em {d['distancia_km'].notna().sum()}. Distância soma apenas os registros disponíveis.")

st.subheader('Distribuição nas zonas')
z = d.loc[d['tem_zonas']]
st.caption(f'Zonas HRR disponíveis em {len(z)} de {len(d)} atividades selecionadas. Registros sem informação de zonas ficam fora destes gráficos.')
if z.empty:
    st.info('Não há registros HRR de cinco zonas com tempo positivo neste recorte.')
else:
    modo = st.radio('Exibir distribuição em', ['Horas', 'Percentual'], horizontal=True)
    totais = z[[f'z{i}_s' for i in range(1, 6)]].sum()
    fig = distribuicao(totais, modo == 'Percentual')
    st.pyplot(fig)
    plt.close(fig)
    st.caption('Percentuais calculados sobre a soma do tempo registrado nas zonas, ponderados pela duração. Essa soma pode diferir do tempo total da atividade.')
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
    st.caption('Semanas começam na segunda-feira. Espaços sem barras indicam ausência de tempo de zonas disponível; não comprovam ausência de exercício. Os períodos nas bordas podem estar incompletos.')
    with st.expander('Ver valores das zonas'):
        resumo = pd.DataFrame({'Zona': [f'Z{i}' for i in range(1, 6)], 'Minutos': totais.to_numpy()/60, 'Percentual': totais.to_numpy()/totais.sum()*100})
        st.dataframe(resumo.round(2), hide_index=True, width='stretch')

st.subheader('Atividades selecionadas')
visiveis = ['Date', 'Time', 'exercicio', 'Total Time', 'Distance', 'Avg. Heart Rate', 'TRIMP', 'RPE', 'periodo', 'tem_zonas']
visiveis = [c for c in visiveis if c in d]
st.dataframe(d.sort_values(['data', 'Time'], ascending=False)[visiveis].rename(columns={
    'Date': 'Data', 'Time': 'Hora', 'exercicio': 'Exercício', 'Total Time': 'Duração',
    'Distance': 'Distância', 'Avg. Heart Rate': 'FC média', 'periodo': 'Período do dispositivo', 'tem_zonas': 'Zonas disponíveis'
}), hide_index=True, width='stretch')
colunas_originais = [c for c in d if c not in ['data', 'exercicio', 'duracao_s', 'distancia_km', 'zonas_n', 'zonas_s', 'tem_zonas', 'periodo'] and not (c.startswith('z') and c.endswith('_s'))]
st.download_button('Baixar atividades filtradas (CSV)', d[colunas_originais].to_csv(index=False, sep=';').encode('utf-8-sig'), file_name='treinos_filtrados.csv', mime='text/csv')
