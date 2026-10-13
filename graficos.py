import numpy as np
import matplotlib.pyplot as plt
from dados import CORES

def distribuicao(totais, percentual=False):
    valores = totais.to_numpy(dtype=float)
    valores = valores / valores.sum() * 100 if percentual else valores / 3600
    fig, ax = plt.subplots(figsize=(9, 3.5))
    ax.barh(['Z1', 'Z2', 'Z3', 'Z4', 'Z5'], valores, color=CORES)
    ax.invert_yaxis()
    ax.set_xlabel('Percentual do tempo nas zonas (%)' if percentual else 'Tempo nas zonas (horas)')
    for i, v in enumerate(valores): ax.text(v, i, f'  {v:.1f}' + ('%' if percentual else ' h'), va='center')
    ax.set_xlim(0, max(valores) * 1.22 if max(valores) else 1)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    return fig

def historico(tabela, percentual=False):
    valores = tabela.to_numpy(dtype=float)
    if percentual:
        totais = valores.sum(axis=1, keepdims=True)
        valores = np.divide(valores * 100, totais, out=np.zeros_like(valores), where=totais > 0)
    else: valores = valores / 60
    fig, ax = plt.subplots(figsize=(11, 4.2))
    base = np.zeros(len(tabela))
    for i in range(5):
        ax.bar(np.arange(len(tabela)), valores[:, i], bottom=base, label=f'Z{i+1}', color=CORES[i])
        base += valores[:, i]
    passo = max(1, int(np.ceil(len(tabela) / 16)))
    indices = np.arange(0, len(tabela), passo)
    ax.set_xticks(indices, [tabela.index[i] for i in indices], rotation=45, ha='right')
    ax.set_ylabel('Tempo nas zonas (%)' if percentual else 'Tempo nas zonas (minutos)')
    ax.legend(ncol=5, loc='upper left', bbox_to_anchor=(0, 1.16), frameon=False)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    return fig
