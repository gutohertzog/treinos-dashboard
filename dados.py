from io import StringIO
import re
import pandas as pd

TIPOS = {'Outdoor Running': 'Corrida ao ar livre', 'Indoor Running': 'Corrida na esteira',
         'Outdoor Walking': 'Caminhada ao ar livre', 'Indoor Walking': 'Caminhada interna',
         'Outdoor Cycling': 'Ciclismo ao ar livre', 'Indoor Cycling': 'Ciclismo interno',
         'Strength Training': 'Musculação', 'Elliptical': 'Elíptico', 'Stair Stepper': 'Escada',
         'Hiking': 'Trilha', 'Dive': 'Mergulho'}
PERIODOS = ['Antes da Mi Band', 'Xiaomi Mi Band 4', 'Apple Watch Series 3', 'Apple Watch Series 11']
CORES = ['#60a5fa', '#34d399', '#facc15', '#fb923c', '#f87171']

def segundos(valor):
    m = re.fullmatch(r'\s*(\d+)h:(\d+)m:(\d+)s\s*', str(valor))
    return sum(int(v) * k for v, k in zip(m.groups(), [3600, 60, 1])) if m else float('nan')

def numero(serie):
    return pd.to_numeric(serie.astype(str).str.replace(',', '.', regex=False)
                         .str.extract(r'([-+]?\d+(?:\.\d+)?)')[0], errors='coerce')

def carregar(conteudo):
    texto = conteudo.decode('utf-8-sig')
    df = pd.read_csv(StringIO(texto), sep=';', dtype=str)
    exigidos = ['Date', 'Time', 'Type', 'Total Time', 'HR Zone Count'] + [f'HRZ{i}' for i in range(1, 6)]
    faltam = set(exigidos) - set(df.columns)
    if faltam:
        raise ValueError('Colunas ausentes: ' + ', '.join(sorted(faltam)))
    duplicados = 0
    if 'UUID' in df:
        identificados = df['UUID'].notna() & df['UUID'].str.strip().ne('')
        repetidos = identificados & df['UUID'].duplicated()
        duplicados = int(repetidos.sum())
        df = df.loc[~repetidos].copy()
    df['data'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
    invalidas = int(df['data'].isna().sum())
    df = df.dropna(subset=['data']).copy()
    df['exercicio'] = df['Type'].map(TIPOS).fillna(df['Type'])
    df['duracao_s'] = df['Total Time'].map(segundos)
    df['distancia_km'] = numero(df['Distance']) if 'Distance' in df else float('nan')
    df['zonas_n'] = numero(df['HR Zone Count'])
    for i in range(1, 6): df[f'z{i}_s'] = df[f'HRZ{i}'].map(segundos)
    df['zonas_s'] = df[[f'z{i}_s' for i in range(1, 6)]].sum(axis=1, min_count=5)
    # A versão inicial aceita apenas registros HRR de cinco zonas.
    metodo = df['HR Zone Type'].eq('HRR') if 'HR Zone Type' in df else False
    df['tem_zonas'] = metodo & df['zonas_n'].eq(5) & df['zonas_s'].gt(0)
    df['periodo'] = PERIODOS[0]
    for limite, nome in zip(['2019-11-05', '2020-03-11', '2026-03-21'], PERIODOS[1:]):
        df.loc[df['data'].ge(pd.Timestamp(limite)), 'periodo'] = nome
    return df.sort_values(['data', 'Time']), {'duplicados': duplicados, 'datas_invalidas': invalidas}

def agrupar_zonas(df, agrupamento):
    colunas = [f'z{i}_s' for i in range(1, 6)]
    d = df.loc[df['tem_zonas']].copy()
    if agrupamento == 'Treino':
        d = d.sort_values(['data', 'Time'])
        resultado = d.set_index(d['data'].dt.strftime('%d/%m/%Y') + ' ' + d['Time'])[colunas]
    else:
        inicio = d['data'].dt.to_period('W-SUN' if agrupamento == 'Semana' else 'M').dt.start_time
        resultado = d.groupby(inicio)[colunas].sum()
        if not resultado.empty:
            indice = pd.date_range(resultado.index.min(), resultado.index.max(), freq='W-MON' if agrupamento == 'Semana' else 'MS')
            resultado = resultado.reindex(indice, fill_value=0)
        resultado.index = resultado.index.strftime('%d/%m/%Y' if agrupamento == 'Semana' else '%m/%Y')
    return resultado
