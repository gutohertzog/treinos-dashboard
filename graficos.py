"""Gráficos matplotlib. Cada função devolve uma Figure (quem chama fecha com plt.close)."""
import matplotlib.pyplot as plt
import numpy as np

from config import CORES, ZONAS


def distribuicao(totais, percentual=False):
    """Barras horizontais com o tempo total (h) ou o percentual em cada zona."""
    valores = totais.to_numpy(dtype=float)
    valores = valores / valores.sum() * 100 if percentual else valores / 3600
    sufixo = '%' if percentual else ' h'

    fig, ax = plt.subplots(figsize=(9, 3.5))
    ax.barh(ZONAS, valores, color=CORES)
    ax.invert_yaxis()
    ax.set_xlabel('Percentual do tempo nas zonas (%)' if percentual else 'Tempo nas zonas (horas)')
    for i, v in enumerate(valores):
        ax.text(v, i, f'  {v:.1f}{sufixo}', va='center')
    ax.set_xlim(0, max(valores) * 1.22 if max(valores) else 1)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    return fig


def _para_percentual(valores):
    """Normaliza cada linha para somar 100. Linhas zeradas continuam zeradas."""
    totais = valores.sum(axis=1, keepdims=True)
    return np.divide(valores * 100, totais, out=np.zeros_like(valores), where=totais > 0)


def _ajustar_rotulos_x(ax, rotulos, max_rotulos=16):
    """Mostra no máximo ~max_rotulos rótulos no eixo X, espaçados igualmente."""
    passo = max(1, int(np.ceil(len(rotulos) / max_rotulos)))
    posicoes = np.arange(0, len(rotulos), passo)
    ax.set_xticks(posicoes, [rotulos[i] for i in posicoes], rotation=45, ha='right')


def historico(tabela, percentual=False):
    """Barras empilhadas por zona ao longo do tempo (minutos ou percentual)."""
    valores = tabela.to_numpy(dtype=float)
    valores = _para_percentual(valores) if percentual else valores / 60

    fig, ax = plt.subplots(figsize=(11, 4.2))
    x = np.arange(len(tabela))
    base = np.zeros(len(tabela))
    for i, zona in enumerate(ZONAS):
        ax.bar(x, valores[:, i], bottom=base, label=zona, color=CORES[i])
        base += valores[:, i]

    _ajustar_rotulos_x(ax, list(tabela.index))
    ax.set_ylabel('Tempo nas zonas (%)' if percentual else 'Tempo nas zonas (minutos)')
    ax.legend(ncol=5, loc='upper left', bbox_to_anchor=(0, 1.16), frameon=False)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    return fig

