---
layout: default
---

# TaxiGov na semana

## O programa

O TaxiGov é um programa do governo federal para transporte de pessoas,
em geral servidores públicos, usando serviços de táxi comum da cidade
onde está localizado o órgão público. Para maiores informações sobre o
TaxiGov, consulte o
[portal gov.br](https://www.gov.br/economia/pt-br/assuntos/gestao/central-de-compras/taxigov).

## Os dados

Os dados do programa estão disponíveis como dados abertos no
[portal dados.gov.br](https://dados.gov.br/dataset/corridas-do-taxigov).

## O código

O código deste site é software livre e encontra-se disponível
[no Github](https://github.com/economiagovbr/taxigovviz).

Feito com Python, Pandas e Folium.

## As visualizações

A seguir, são apresentadas algumas visualizações sobre os dados dos
últimos 7 dias.

### Mapa de calor

Os dados dos últimos 7 dias podem ser visualizados como mapa de calor.

<iframe
    src="maps/heatmap.html"
    title="mapa de calor"
    width="800"
    height="600">
</iframe>

Ver [este mapa em tela cheia](maps/heatmap.html).

E também em uma animação por cada dia, dentre os últimos 7 dias.

<iframe
    src="maps/heatmap-time.html"
    title="mapa de calor por tempo"
    width="800"
    height="600">
</iframe>

Ver [este mapa em tela cheia](maps/heatmap-time.html).

### Com agrupamentos

Para dar uma melhor ideia de volume, os pontos podem ser juntados em
agrupamentos (*clusters*).

Ao aproximar a visualização do mapa, esses agrupamentos vão se dividir
automaticamente para melhor se acomodar à janela de visualização. Ao
aproximar o mapa suficientemente, será possível visualizar os pontos de
partida e de chegada individualmente. Clicando-se esses pontos, é
possível visualizar mais dados sobre aquela corrida.

Atenção ao fato de que há pontos de partida e pontos de chegada, então o
número de corridas em geral, quando se afasta a visualização, será a
metade do número representado.

<iframe
    src="maps/clusters.html"
    title="mapa de agrupamentos"
    width="800"
    height="600">
</iframe>

Ver [este mapa em tela cheia](maps/clusters.html).

### Por órgão

Selecione o ícone de camadas no canto superior direito do mapa para
selecionar um ou mais órgãos. As corridas dos órgãos selecionados
serão exibidas com marcadores individuais.

Os pontos de partida estão representados em azul e os pontos de chegada
em laranja.

<iframe
    src="maps/orgaos.html"
    title="mapa por órgão"
    width="800"
    height="600">
</iframe>

Ver [este mapa em tela cheia](maps/orgaos.html).

Página atualizada automaticamente em:
{{ site.time | date: '%Y-%m-%d %H:%M:%S' }} (UTC).
