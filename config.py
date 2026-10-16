"""Constantes compartilhadas pelo app."""

ZONAS = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']
COLUNAS_ZONAS = [f'z{i}_s' for i in range(1, 6)]  # tempo (s) em cada zona, criadas em dados.py
CORES = ['#60a5fa', '#34d399', '#facc15', '#fb923c', '#f87171']

TIPOS = {
    'Outdoor Running': 'Corrida ao ar livre',
    'Indoor Running': 'Corrida na esteira',
    'Outdoor Walking': 'Caminhada ao ar livre',
    'Indoor Walking': 'Caminhada interna',
    'Outdoor Cycling': 'Ciclismo ao ar livre',
    'Indoor Cycling': 'Ciclismo interno',
    'Strength Training': 'Musculação',
    'Elliptical': 'Elíptico',
    'Stair Stepper': 'Escada',
    'Hiking': 'Trilha',
    'Dive': 'Mergulho',
}

PERIODOS = ['Antes da Mi Band', 'Xiaomi Mi Band 4', 'Apple Watch Series 3', 'Apple Watch Series 11']

# (data de início, período). O primeiro período (PERIODOS[0]) vale antes da primeira data.
MARCOS_DISPOSITIVO = [
    ('2019-11-05', PERIODOS[1]),
    ('2020-03-11', PERIODOS[2]),
    ('2026-03-21', PERIODOS[3]),
]

COLUNAS_OBRIGATORIAS = ['Date', 'Time', 'Type', 'Total Time', 'HR Zone Count'] + [f'HRZ{i}' for i in range(1, 6)]

