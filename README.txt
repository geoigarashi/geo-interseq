================================================================================
 GeoInterseQ
 Versão 1.1.7  |  Autores: Marcelo Seiji de Melo Matsumura, Clayton Igarashi
================================================================================

DESCRIÇÃO
---------
Plugin QGIS para calcular a área de interseção e o percentual de sobreposição
entre uma camada base de polígonos vetoriais e múltiplas camadas analisadas
(vetoriais ou raster).

Funcionalidades:
  - Análise vetor × vetor: por feição, com campo de rótulo configurável
  - Análise vetor × raster: por classe (raster categórico inteiro), com
    paridade numérica em relação ao InfoGEO
  - Dois modos de percentual: % da feição analisada ou % da camada base
  - Geração de camada de interseção temporária com simbologia do raster
  - Exportação dos resultados em CSV (separador ";", UTF-8 BOM)


REQUISITOS
----------

1. QGIS >= 3.16 (obrigatório para qualquer uso)
   Inclui automaticamente: GDAL/OGR, numpy, PyQt5

2. Para análise de camadas RASTER (obrigatório):
   - rasterio
   - shapely
   - pyproj

   Se alguma dessas bibliotecas estiver ausente, o plugin exibirá um aviso ao
   ser carregado no QGIS. A análise vetorial continuará funcionando normalmente.


INSTALAÇÃO DAS DEPENDÊNCIAS
----------------------------

Opção A — OSGeo4W Shell (recomendado para instalações OSGeo4W/QGIS standalone)
  1. Abra o "OSGeo4W Shell" como Administrador
  2. Execute:
       pip install rasterio shapely pyproj

Opção B — Console Python do QGIS (Plugins > Console Python)
  Execute linha a linha:
       import subprocess, sys
       subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'rasterio', 'shapely', 'pyproj'])

Opção C — Instalador avançado do OSGeo4W
  Busque e marque os pacotes:
       python-rasterio
       python-shapely
       python-pyproj

Após instalar, reinicie o QGIS.


INSTALAÇÃO DO PLUGIN
--------------------
  Plugins > Gerenciar e Instalar Plugins > Instalar a partir de arquivo ZIP
  Selecione o arquivo GeoInterseQ_vX.X.X.zip


SUPORTE
-------
  Mantenedor: Clayton Igarashi <geoigarashi@gmail.com>
================================================================================
