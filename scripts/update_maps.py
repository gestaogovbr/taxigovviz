#!/usr/bin/python
"""Script para atualizar os mapas Folium na visualização de dados.

Para usar:

$ ./update_maps.py --path [output_path]

Parâmetros:

    output_path     Diretório de saída para os arquivos gerados
"""

import os
import argparse

import pandas as pd
import folium

def generate_maps(path: str):
    print ("path: ", path)

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
