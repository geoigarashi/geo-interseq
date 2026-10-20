# 🌐 GeoInterseQ — v1.4.2: Normalização Bilateral e Fechamento Contábil de Áreas Raster

## 🚀 Destaques da Versão

* **Fechamento Contábil Exato (100,0000%):** Implementação de regra de normalização proporcional bilateral na soma das classes raster em relação à área plana UTM do polígono base.
* **Eliminação de Resíduos de Densificação Cartográfica:** Compensa a distorção métrica microscópica (~1,5 ppm ou ~0,00015%) decorrente da densificação de vértices na reprojeção do recorte fatiado de `EPSG:4326` para `SIRGAS 2000 / UTM`.
* **Paridade Absoluta com InfoGEO (`infogeo-valoracao`):** Harmonização rigorosa com a regra contábil do motor de valoração (`discretization_ratio <= 0.005`), garantindo `0,0000 ha` de divergência até a 4ª casa decimal entre os relatórios CSV do GeoInterseQ e laudos de avaliação agronômica.
* **Proteção de Interseções Parciais:** Limite seguro de tolerância (0,5%) que impede a expansão indevida de sobreposições incompletas ou rasters que cobrem apenas frações da gleba.
* **Arquitetura Desacoplada e Testável (SOLID):** Função `normalize_class_areas()` adicionada ao módulo puro `percent_utils.py` com cobertura completa de testes unitários automatizados (sem dependência da interface QGIS).

---

## 🎯 Justificativa Cartográfica e Técnica

Quando uma camada base em coordenadas geográficas (`EPSG:4326`) é projetada para UTM, seus segmentos retos mantêm a curvatura geodésica entre vértices originais. Já a máscara raster vetorizada é fatiada a cada ~10 m (tamanho do pixel) e recortada pelo polígono base.

Essa densificação de milhares de vértices intermediários ao longo do perímetro, ao ser projetada para a grade plana UTM (Transversa de Mercator), gera uma soma ligeiramente inferior (cerca de 0,0041 ha em 2.732 ha). Com o fechamento contábil bilateral acionado quando o desvio residual for $\le 0,5\%$, a soma das classes fecha com exatidão em 100% da área do imóvel rural, eliminando discrepâncias contábeis em auditorias de crédito rural.

---

## 📋 Changelog Detalhado

### Correções e Paridade Numérica
- **Fechamento Bilateral em `geo_interseq.py`:** Substituição do ajuste unilateral de excesso (`> 1.0001`) pela normalização bilateral proporcional quando `discretization_ratio <= 0.005` ou `area_classes_total > base_area`.
- **Módulo `percent_utils.py`:** Adição da função `normalize_class_areas()` com tipagem estrita Python 3.12+ (PEP 585/604) e tratamento defensivo para áreas nulas ou vazias.
- **Suíte de Testes Unitários (`tests/test_percent_utils.py`):** Adição de 4 novos testes unitários cobrindo paridade com dados reais de laudo, preservação de coberturas parciais, contenção de excesso e casos limítrofes (zero/vazio).

---

## ⚙️ Requisitos & Compatibilidade

- **QGIS:** 3.16 até 3.99+.
- **Python:** 3.12+ (ambiente padrão Conda `geocore`).
- **Bibliotecas:** `rasterio`, `shapely`, `pyproj` (instaláveis via assistente integrado do plugin com 1 clique).

---

## 📦 Instruções de Instalação via ZIP

1. No QGIS, acesse o menu **Complementos** → **Gerenciar e Instalar Complementos...**
2. Clique na aba lateral **Instalar a partir do ZIP**.
3. Clique em **Buscar...** e selecione o arquivo:
   `c:\Python\QGIS Plugins\plugins_zip\geointerseq_v1.4.2.zip`
4. Clique em **Instalar Complemento**.
5. O GeoInterseQ estará disponível no menu **Ferramentas Geo** e na barra de ferramentas.
