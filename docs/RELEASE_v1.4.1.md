# 🌐 GeoInterseQ — v1.4.1: Alinhamento Exato da Grade Raster e Paridade Numérica com GDAL

## 🚀 Destaques da Versão

* **Ancoragem à Grade Inteira:** A janela de leitura do raster (`rasterio.windows.Window`) agora ancora estritamente seus limites (`col_off`, `row_off`, `width`, `height`) nos índices inteiros da grade matricial nativa do GeoTIFF.
* **Eliminação da Translação Afim Sub-Pixel:** A origem `(c, f)` da matriz de transformação afim do recorte (`window_affine`) coincide exatamente (`erro = 0,00 m`) com a coordenada nativa do pixel raster, eliminando o deslocamento espacial de até 1 pixel (`~10 m` em rasters de 10 m) na vetorização com `rasterio.features.shapes`.
* **Supressão da Reamostragem Silenciosa do GDAL:** Ao receber limites estritamente inteiros, o motor C/C++ `GDALRasterIOEx` executa leitura direta de blocos (*raw block copy*) sem acionar interpolação *Nearest Neighbor* espúria nos limites internos entre classes de uso do solo.
* **Margem de Segurança de 1 Pixel:** Buffer automático de 1 pixel (`max(abs(a), abs(e))`) com discretização defensiva (`math.floor` para o canto inicial e `math.ceil` para o canto final), garantindo cobertura total de pixels limítrofes do polígono de entrada.
* **Paridade Numérica com Ground Truth:** Áreas calculadas em hectares por classe alcançam paridade com a ferramenta oficial `rasterio.mask.mask` e plataforma `infogeo-valoracao`.
* **Arquitetura Desacoplada (SOLID):** Criação do módulo puro `raster_window.py` isolado da UI PyQt5/QGIS, viabilizando execução e testes unitários automatizados em qualquer ambiente Python.

---

## 🎯 Justificativa Técnica (Auditoria Geoespacial e Crédito Rural)

Em auditorias de sobreposição de uso do solo (ex.: MapBiomas, PRODES) sobre glebas rurais, a leitura de janelas com coordenadas fracionárias (`from_bounds`) causava duas distorções acumuladas:
1. Uma translação sub-pixel da matriz afim, deslocando os polígonos das classes em relação ao polígono do imóvel no momento da operação `intersection()`.
2. Uma reamostragem *Nearest Neighbor* não solicitada executada pelo driver GDAL ao preencher buffers discretos a partir de coordenadas contínuas, modificando classes categóricas nas transições.

Com a ancoragem em índices inteiros e margem de 1 pixel, o alinhamento espacial é absoluto e o cálculo de áreas por classe atinge exatidão submétrica.

---

## 📋 Changelog Detalhado

### Novos Recursos
- Módulo `raster_window.py` com a função `align_raster_window()`, desacoplada do runtime QGIS/PyQt.
- Suíte de testes unitários `tests/test_raster_window.py` cobrindo tipagem inteira, invariância da origem afim, cobertura espacial com buffer e contenção por limites do raster.

### Correções de Bugs
- **Correção da Janela Raster em `geo_interseq.py`:** Substituição da leitura direta de `from_bounds()` pela função `align_raster_window()`, eliminando o desvio sub-pixel de até 1 pixel em X e Y.
- **Tratamento de Borda:** Prevenção de perda de pixels extremos com adição de buffer de 1 pixel antes do cálculo da extensão da janela.

---

## ⚙️ Requisitos & Dependências

- **QGIS:** 3.16 ou superior.
- **Python:** 3.12+ (ambiente padrão Conda `geocore`).
- **Bibliotecas:** `rasterio`, `shapely`, `pyproj` (instaláveis via assistente com 1 clique integrado ao plugin).

---

## 📦 Instruções de Instalação via ZIP

1. No QGIS, acesse o menu **Complementos** → **Gerenciar e Instalar Complementos...**
2. Clique na aba lateral **Instalar a partir do ZIP**.
3. Clique em **Buscar...** e selecione o arquivo:
   `c:\Python\QGIS Plugins\plugins_zip\geointerseq_v1.4.1.zip`
4. Clique em **Instalar Complemento**.
5. O GeoInterseQ estará disponível no menu **Ferramentas Geo** e na barra de ferramentas.
