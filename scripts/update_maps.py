#!/usr/bin/python
"""Script para atualizar os mapas Folium na visualização de dados.
"""

import os, pathlib
import argparse
from datetime import datetime
from collections import defaultdict, OrderedDict, namedtuple

import pandas as pd
import numpy as np

import folium
from folium.plugins import HeatMap, HeatMapWithTime

DATA_URL = 'http://repositorio.dados.gov.br/seges/taxigov/taxigov-corridas-7-dias.zip'
MAPS_SUBFOLDER = 'maps'

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    "Limpa os dados, corrigindo problemas de qualidade de dados na origem."

    for point_type in ('origem', 'destino_solicitado', 'destino_efetivo'):
        # coordenadas como string e com vírgula como separador decimal
        for axis in ('latitude', 'longitude'):
            column = '_'.join((point_type, axis))
            if df[column].dtype == 'object':
                df[column] = df[column].str.replace(',','.')
                df[column] = df[column].astype(float)

        # coordenadas com valores inválidos
        latitude_inexistente = (df[f'{point_type}_latitude'] < -90.0), f'{point_type}_latitude'
        longitude_inexistente = (df[f'{point_type}_longitude'] < -180.0), f'{point_type}_longitude'
        df.loc[latitude_inexistente] = df.loc[latitude_inexistente] / 100000.0
        df.loc[longitude_inexistente] = df.loc[longitude_inexistente] / 100000.0

        # coordenadas no hemisfério errado
        latitude_fora_hemisferio = (df[f'{point_type}_latitude'] > 0.0), f'{point_type}_latitude'
        longitude_fora_hemisferio = (df[f'{point_type}_longitude'] > 0.0), f'{point_type}_longitude'
        df.loc[latitude_fora_hemisferio] = df.loc[latitude_fora_hemisferio] * -1.0
        df.loc[longitude_fora_hemisferio] = df.loc[longitude_fora_hemisferio] * -1.0

    # converte o que não for numérico
    numeric_columns = ['origem_latitude', 'origem_longitude',
        'destino_solicitado_latitude', 'destino_solicitado_longitude',
        'destino_efetivo_latitude', 'destino_efetivo_longitude']
    for column in numeric_columns:
        if df[column].dtype != 'float64':
            df[column] = df[column].apply(
                lambda s: pd.to_numeric(s) if isinstance(s, str) else s)

    return df

def get_data(url: str) -> pd.DataFrame:
    "Obtém o data frame a partir da origem dos dados."

    df = pd.read_csv(url, compression='zip')
    return clean_data(df)

def marker_popup(corrida: namedtuple, tipo: str) -> str:
    "Retorna o conteúdo formatado de um marcador."

    markup = {
        'partida': (
            '<dl>'
            f'<dt>Hora partida:<dt><dd>{corrida.data_inicio}</dd>'
            '<dt>Destino efetivo:<dt>'
            f'<dd>{corrida.destino_efetivo_endereco}</dd>'
            f'<dt>Órgão:</dt><dd>{corrida.nome_orgao}</dd>'
            f'<dt>Motivo:</dt><dd>{corrida.motivo_corrida}</dd>'
            f'<dt>Distância:</dt><dd>{corrida.km_total}</dd>'
            f'<dt>Valor:</dt><dd>{corrida.valor_corrida}</dd>'
            '</dl>'
        ),
        'chegada': (
            '<dl>'
            f'<dt>Hora chegada:</dt><dd>{corrida.data_final}</dd>'
            f'<dt>Origem:<dt><dd>{corrida.origem_endereco}</dd>'
            f'<dt>Órgão:</dt><dd>{corrida.nome_orgao}</dd>'
            f'<dt>Motivo:</dt><dd>{corrida.motivo_corrida}</dd>'
            f'<dt>Distância:</dt><dd>{corrida.km_total}</dd>'
            f'<dt>Valor:</dt><dd>{corrida.valor_corrida}</dd>'
            '</dl>'
        ),
    }
    return markup[tipo]

def fares_map(df: pd.DataFrame) -> folium.Map:
    "Cria um mapa de corridas com marcadores individuais."

    m = folium.Map(
        location=(
            (df.origem_latitude.mean()
                + df.destino_efetivo_latitude.mean()) / 2,
            (df.origem_longitude.mean()
                + df.destino_efetivo_longitude.mean()) / 2
        ),
        zoom_start=11
    )

    for corrida in df.itertuples():
        coordinates = (corrida.origem_latitude, corrida.origem_longitude)
        if not np.isnan(coordinates).any():
            folium.Marker(
                coordinates,
                popup=marker_popup(corrida, 'partida'),
                icon=folium.Icon(
                    color='darkblue', icon='glyphicon glyphicon-log-out')
            ).add_to(m)
        coordinates = (
            corrida.destino_efetivo_latitude,
            corrida.destino_efetivo_longitude)
        if not np.isnan(coordinates).any():
            folium.Marker(
                coordinates,
                popup=marker_popup(corrida, 'chegada'),
                icon=folium.Icon(
                    color='orange', icon='glyphicon glyphicon-log-in')
            ).add_to(m)

    return m

def fares_map_cluster(df: pd.DataFrame) -> folium.Map:
    "Cria um mapa de corridas com agrupamentos."

    m = folium.Map(
        location=(
            (df.origem_latitude.mean()
                + df.destino_efetivo_latitude.mean()) / 2,
            (df.origem_longitude.mean()
                + df.destino_efetivo_longitude.mean()) / 2
        ),
        zoom_start=5
    )
    
    marker_cluster = folium.plugins.MarkerCluster().add_to(m)

    for corrida in df.itertuples():
        coordinates = (corrida.origem_latitude, corrida.origem_longitude)
        if not np.isnan(coordinates).any():
            folium.Marker(
                coordinates,
                popup=marker_popup(corrida, 'partida'),
                icon=folium.Icon(
                    color='darkblue', icon='glyphicon glyphicon-log-out')
            ).add_to(marker_cluster)
        coordinates = (
            corrida.destino_efetivo_latitude,
            corrida.destino_efetivo_longitude)
        if not np.isnan(coordinates).any():
            folium.Marker(
                coordinates,
                popup=marker_popup(corrida, 'chegada'),
                icon=folium.Icon(
                    color='orange', icon='glyphicon glyphicon-log-in')
            ).add_to(marker_cluster)

    return m

def fares_map_category(df: pd.DataFrame, category_column: str) -> folium.Map:
    """Cria um mapa de corridas com uma camada para cada item da categoria
    especificada.

    category_column:    a coluna da qual serão tomados os valores para camadas
    """

    m = folium.Map(
        location=(
            (df.origem_latitude.mean()
                + df.destino_efetivo_latitude.mean()) / 2,
            (df.origem_longitude.mean()
                + df.destino_efetivo_longitude.mean()) / 2
        ),
        zoom_start=5
    )

    group = {}
    for category in df[category_column].unique():
        feature_group = folium.FeatureGroup(category, show=False)
        feature_group.add_to(m)
        group[category] = feature_group

    for corrida in df.itertuples():
        coordinates = (corrida.origem_latitude, corrida.origem_longitude)
        if not np.isnan(coordinates).any():
            folium.Marker(
                coordinates,
                popup=marker_popup(corrida, 'partida'),
                icon=folium.Icon(color='darkblue', icon='glyphicon glyphicon-log-out')
            ).add_to(group[getattr(corrida,category_column)])
        coordinates = (corrida.destino_efetivo_latitude, corrida.destino_efetivo_longitude)
        if not np.isnan(coordinates).any():
            folium.Marker(
                coordinates,
                popup=marker_popup(corrida, 'chegada'),
                icon=folium.Icon(color='orange', icon='glyphicon glyphicon-log-in')
            ).add_to(group[getattr(corrida,category_column)])

    folium.LayerControl().add_to(m)

    return m

def heat_map(df: pd.DataFrame, point_type: str) -> folium.Map:
    """Cria um mapa de calor.

    point_type: o prefixo do par de colunas a serem usadas como ponto
    """

    m = folium.Map(
        location=(
            (df[f'{point_type}_latitude'].mean()
                + df.destino_efetivo_latitude.mean()) / 2,
            (df[f'{point_type}_longitude'].mean()
                + df.destino_efetivo_longitude.mean()) / 2
        ),
        zoom_start=11
    )
    
    df_notna = (
        df
        .loc[df[f'{point_type}_latitude'].notna()] # tira os nulos
        .loc[df[f'{point_type}_longitude'].notna()] # tira os nulos
        .loc[df['data_inicio'].notna()] # tira os nulos
    )

    HeatMap(
        df_notna
        .loc[:,[f'{point_type}_latitude', f'{point_type}_longitude']]
    ).add_to(m)

    return m

def heat_map_with_time(df: pd.DataFrame, point_type: str) -> folium.Map:
    """Cria um mapa de calor com animação de tempo.

    point_type: o prefixo do par de colunas a serem usadas como ponto
    """

    m = folium.Map(
        location=(
            (df[f'{point_type}_latitude'].mean()
                + df.destino_efetivo_latitude.mean()) / 2,
            (df[f'{point_type}_longitude'].mean()
                + df.destino_efetivo_longitude.mean()) / 2
        ),
        zoom_start=6
    )
    
    # tira os nulos
    df_notna = (
        df
        .loc[df[f'{point_type}_latitude'].notna()]
        .loc[df[f'{point_type}_longitude'].notna()]
        .loc[df['data_inicio'].notna()]
    )
    
    # prepara estrutura de dados do HeatMapWithTime
    data = defaultdict(list)
    for index, row in df_notna.iterrows():
        data[datetime.fromisoformat(row['data_inicio']).date().strftime("%Y-%m-%d")].append([
            row[f'{point_type}_latitude'],
            row[f'{point_type}_longitude']
        ])
    data = OrderedDict(sorted(data.items(), key=lambda t: t[0]))
    
    HeatMapWithTime(
        data=list(data.values()),
        index=list(data.keys()),
        auto_play=True,
    ).add_to(m)

    return m

def generate_maps(path: str):
    "Gera os mapas em uma subpasta em um caminho especificado."

    maps_folder = os.path.join(path, MAPS_SUBFOLDER)
    pathlib.Path(maps_folder).mkdir(exist_ok=True)

    # obtém os dados
    df = get_data(DATA_URL)

    # Mapa de calor geral
    m = heat_map(df, 'destino_efetivo')
    m.fit_bounds(m.get_bounds())
    m.save(os.path.join(maps_folder, 'heatmap.html'))

    # Mapa de calor por dia
    m = heat_map_with_time(df, 'destino_efetivo')
    m.save(os.path.join(maps_folder, 'heatmap-time.html'))

    # Mapa de agrupamentos (clusters)
    m = fares_map_cluster(df)
    m.save(os.path.join(maps_folder, 'clusters.html'))

    # Mapa por órgão
    m = fares_map_category(df, 'nome_orgao')
    m.save(os.path.join(maps_folder, 'orgaos.html'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__
    )
    parser.add_argument(
        "--path",
        help="Diretório de saída para os arquivos gerados",
        nargs=1,
        metavar="OUTPUT_PATH",
    )

    args = parser.parse_args()

    if args.path:
        generate_maps(args.path[0])
    else:
        parser.print_help()
