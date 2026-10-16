# treinos-dashboard

Painel pessoal em Streamlit com gráficos Matplotlib.

## Executar no Linux

Dentro da pasta extraída:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Abra o endereço local indicado pelo Streamlit. Para encerrar, pressione Ctrl+C no terminal.

## Uso

- A seleção inicial mostra corridas nos últimos 90 dias do arquivo.
- Selecione exercícios, datas e períodos dos dispositivos na lateral.
- Compare zonas em horas ou percentuais; agrupe o histórico por treino, semana ou mês.
- Consulte os registros e baixe o CSV do recorte.
- Substitua workouts.csv por uma exportação nova ou carregue outro CSV na lateral. O formato esperado é UTF-8, separado por ponto e vírgula, com os cabeçalhos da exportação fornecida.

## Critérios

Os períodos dos dispositivos são inferidos pelas datas informadas, sem atribuir o dispositivo real a uma atividade. Mantêm-se os rótulos Z1–Z5 porque o CSV não informa os limites de frequência cardíaca. Comparações históricas pressupõem configurações de zonas comparáveis.

A versão inicial usa dados de cinco zonas HRR com tempo positivo e campos completos. Registros sem essas informações continuam no resumo e na tabela, mas não nos gráficos de zonas. Percentuais usam o tempo total classificado nas zonas, e não a média dos percentuais de cada treino. O tempo nas zonas pode ser menor que a duração do treino.

UUIDs duplicados são removidos na leitura; registros sem UUID não são deduplicados. Datas inválidas são descartadas com aviso. Campos numéricos ausentes permanecem ausentes. Semanas começam na segunda-feira e os períodos nas bordas podem ser parciais.

Os gráficos de distância anual/mensal e o modelo TSB ficam para as próximas versões.

Arquivos: app.py (interface), dados.py (leitura e agrupamento), graficos.py (Matplotlib), workouts.csv (dados), requirements.txt (dependências).

