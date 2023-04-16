#!/usr/bin/python
"""Script para atualizar os mapas Folium na visualização de dados.
"""

import os, pathlib
import argparse
from datetime import datetime
from collections import defaultdict, OrderedDict, namedtuple

import pandas as pd
import numpy as np
from frictionless import Package

import folium
from folium.plugins import HeatMap, HeatMapWithTime

PACKAGE_URL = "https://repositorio.dados.gov.br/seges/taxigov/v2/datapackage.yaml"
RESOURCE_NAME = "corridas-7-dias"
MAPS_SUBFOLDER = 'maps'

def get_data(url: str) -> pd.DataFrame:
    "Obtém o data frame a partir da origem dos dados."

    package = Package(url)
    df = package.get_resource(RESOURCE_NAME).to_pandas()
    return df

def marker_popup(corrida: namedtuple, tipo: str) -> str:
    "Retorna o conteúdo formatado de um marcador."

    corrida_details = (
        f'<dt>Órgão:</dt><dd>{corrida.orgao_nome}</dd>'
        f'<dt>Unidade administrativa:</dt><dd>{corrida.unidade_administrativa_nome}</dd>'
        f'<dt>Status:</dt><dd>{corrida.status}</dd>'
        f'<dt>Motivo:</dt><dd>{corrida.motivo}</dd>'
        f'<dt>Justificativa:</dt><dd>{corrida.justificativa if corrida.justificativa else "-"}</dd>'
        f'<dt>Distância:</dt><dd>{"-" if np.isnan(corrida.km_total) else corrida.km_total}</dd>'
        f'<dt>Valor:</dt><dd>{"-" if np.isnan(corrida.valor_corrida) else corrida.valor_corrida}</dd>'
        f'<dt>Veículo</dt><dd>'
            '<dt>Fabricante / modelo</dt>'
            f'<dd>{corrida.veiculo_fabricante} / {corrida.veiculo_modelo}</dd>'
            '<dt>Ano fabricação / modelo</dt>'
            f'<dd>{corrida.veiculo_ano_fabricacao} / {corrida.veiculo_ano_fabricacao}</dd>'
            f'<dt>Cor</dt><dd>{corrida.veiculo_cor}</dd>'
            f'<dt>Placa</dt><dd>{corrida.veiculo_placa}</dd>'
        '</dd>'
    )

    markup = {
        'partida': (
            '<dl>'
            f'<dt>Hora partida:<dt><dd>{corrida.data_inicio}</dd>'
            '<dt>Destino efetivo:<dt>'
            f'<dd>{corrida.destino_efetivo_endereco if corrida.destino_efetivo_endereco else "-"}</dd>'
            + corrida_details +
            '</dl>'
        ),
        'chegada': (
            '<dl>'
            f'<dt>Hora chegada:</dt><dd>{corrida.data_final}</dd>'
            f'<dt>Origem:<dt><dd>{corrida.origem_endereco}</dd>'
            + corrida_details +
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
        data[row['data_inicio'].date().strftime("%Y-%m-%d")].append([
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
    df = get_data(PACKAGE_URL)

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
    m = fares_map_category(df, 'orgao_nome')
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
