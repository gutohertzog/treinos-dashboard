"""Leitura, limpeza e agrupamento dos dados do CSV de treinos."""
import re
from io import StringIO

import pandas as pd

from config import COLUNAS_OBRIGATORIAS, COLUNAS_ZONAS, MARCOS_DISPOSITIVO, PERIODOS, TIPOS


# ---------- conversões básicas ----------

def segundos(valor):
    """Converte '1h:23m:45s' em segundos. Retorna NaN se o formato não bater."""
    m = re.fullmatch(r'\s*(\d+)h:(\d+)m:(\d+)s\s*', str(valor))
    if not m:
        return float('nan')
    horas, minutos, segs = (int(v) for v in m.groups())
    return horas * 3600 + minutos * 60 + segs


def numero(serie):
    """Extrai o primeiro número de cada texto (aceita vírgula decimal)."""
    texto = serie.astype(str).str.replace(',', '.', regex=False)
    return pd.to_numeric(texto.str.extract(r'([-+]?\d+(?:\.\d+)?)')[0], errors='coerce')


# ---------- etapas do carregamento ----------

def _ler_csv(conteudo):
    df = pd.read_csv(StringIO(conteudo.decode('utf-8-sig')), sep=';', dtype=str)
    faltam = set(COLUNAS_OBRIGATORIAS) - set(df.columns)
    if faltam:
        raise ValueError('Colunas ausentes: ' + ', '.join(sorted(faltam)))
    return df


def _remover_duplicados(df):
    """Remove linhas com UUID repetido. Linhas sem UUID são mantidas."""
    if 'UUID' not in df:
        return df, 0
    tem_uuid = df['UUID'].notna() & df['UUID'].str.strip().ne('')
    repetidos = tem_uuid & df['UUID'].duplicated()
    return df.loc[~repetidos].copy(), int(repetidos.sum())


def _preparar_datas(df):
    df['data'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
    invalidas = int(df['data'].isna().sum())
    return df.dropna(subset=['data']).copy(), invalidas


def _adicionar_colunas_derivadas(df):
    df['exercicio'] = df['Type'].map(TIPOS).fillna(df['Type'])
    df['duracao_s'] = df['Total Time'].map(segundos)
    df['distancia_km'] = numero(df['Distance']) if 'Distance' in df else float('nan')

    df['zonas_n'] = numero(df['HR Zone Count'])
    for i, coluna in enumerate(COLUNAS_ZONAS, start=1):
        df[coluna] = df[f'HRZ{i}'].map(segundos)
    df['zonas_s'] = df[COLUNAS_ZONAS].sum(axis=1, min_count=5)

    # A versão inicial aceita apenas registros HRR de cinco zonas com tempo positivo.
    if 'HR Zone Type' in df:
        metodo_hrr = df['HR Zone Type'].eq('HRR')
    else:
        metodo_hrr = pd.Series(False, index=df.index)
    df['tem_zonas'] = metodo_hrr & df['zonas_n'].eq(5) & df['zonas_s'].gt(0)
    return df


def _classificar_periodo(datas):
    """Associa cada data ao dispositivo em uso, pelas datas de MARCOS_DISPOSITIVO."""
    periodo = pd.Series(PERIODOS[0], index=datas.index)
    for inicio, nome in MARCOS_DISPOSITIVO:
        periodo[datas.ge(pd.Timestamp(inicio))] = nome
    return periodo


def carregar(conteudo):
    """Lê o CSV (bytes) e devolve (DataFrame, avisos)."""
    df = _ler_csv(conteudo)
    df, duplicados = _remover_duplicados(df)
    df, invalidas = _preparar_datas(df)
    df = _adicionar_colunas_derivadas(df)
    df['periodo'] = _classificar_periodo(df['data'])
    avisos = {'duplicados': duplicados, 'datas_invalidas': invalidas}
    return df.sort_values(['data', 'Time']), avisos


# ---------- agrupamento ----------

def agrupar_zonas(df, agrupamento):
    """Tempo (s) por zona, agrupado por 'Treino', 'Semana' ou 'Mês'."""
    d = df.loc[df['tem_zonas']].copy()
    if agrupamento == 'Treino':
        return _zonas_por_treino(d)
    return _zonas_por_periodo(d, semanal=(agrupamento == 'Semana'))


def _zonas_por_treino(d):
    d = d.sort_values(['data', 'Time'])
    rotulos = d['data'].dt.strftime('%d/%m/%Y') + ' ' + d['Time']
    return d.set_index(rotulos)[COLUNAS_ZONAS]


def _zonas_por_periodo(d, semanal):
    inicio = d['data'].dt.to_period('W-SUN' if semanal else 'M').dt.start_time
    resultado = d.groupby(inicio)[COLUNAS_ZONAS].sum()
    if not resultado.empty:
        # Preenche semanas/meses sem dados com zero para o eixo X não "pular" períodos.
        indice = pd.date_range(resultado.index.min(), resultado.index.max(),
                               freq='W-MON' if semanal else 'MS')
        resultado = resultado.reindex(indice, fill_value=0)
    resultado.index = resultado.index.strftime('%d/%m/%Y' if semanal else '%m/%Y')
    return resultado

