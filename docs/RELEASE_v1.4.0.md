# 🌐 GeoInterseQ — v1.4.0: Áreas Planas em UTM/SIRGAS 2000 com Fuso Dinâmico

## ✨ Destaques

* **Cálculo migrado de geodésico para plano UTM:** interseções (GEOS) e áreas agora em metros, na projeção SIRGAS 2000 / UTM do fuso local — paridade com `area($geometry)`, memoriais descritivos e CAD.
* **Fuso dinâmico por par/feição/base**, escolhido pelo centróide (vetor pareado), pelo envelope de sobreposição (vetor convencional) ou pelo centróide da base (raster).
* **Rastreabilidade:** nova coluna **Fuso UTM** na tabela, na camada de saída (`fuso_utm`) e no CSV.
* **Glebas transfronteiriças:** sinalizadas com `(borda)` sem fatiamento da geometria.
* **Camadas de saída no CRS do projeto** (antes EPSG:4326).

## 🎯 Justificativa Técnica (Auditoria de Crédito Rural)

Laudos, peças cartorárias e análises do Proagro/BACEN usam áreas planas em UTM/SIRGAS 2000. A área geodésica elipsoidal diverge da plana UTM em ~0,08% (meridiano central) até >0,30% (bordas do fuso), gerando contestações. Além disso, operar a interseção em graus decimais introduzia assimetria angular e ruído numérico; em metros, `A(A∩B) ≤ min(A(A), A(B))` é satisfeito a menos de ruído de ponto flutuante.

## 📋 Changelog Detalhado

### Features
- Novo módulo `utm_zone.py` (seleção de fuso pura, testável sem QGIS) e `utm_projection.py` (`BaseFootprint`, `UtmTransformCache`).
- Coluna `Fuso UTM` na tabela de resultados, atributo `fuso_utm` e exportação CSV.
- Detecção de gleba transfronteiriça (`(borda)`) e registro em `QgsMessageLog`.

### Refactoring
- `_process_vector_layer`, `_process_vector_layer_paired` e `_process_raster_layer` medem em UTM plana; base mantida no CRS nativo (sem passar por EPSG:4326).
- Remoção de `QgsDistanceArea`.
- Percentuais normalizados por `percent_utils.safe_percent`: ruído de ponto flutuante da interseção (ex.: 99,9999999999817 %) é ajustado para 100 %, com clamp em [0, 100].
- Tolerância do alerta de consistência no modo pareado reduzida de 0,1% para 1e-6 relativo.

### Fixes
- Códigos EPSG SIRGAS 2000 UTM corretos: Sul `31960 + fuso` (17S–25S) e Norte `31954 + fuso` (11N–22N).

### Docs
- README com seção "Metodologia de Cálculo de Área"; painel de ajuda atualizado.

### ⚠️ Mudanças de Comportamento
- Áreas e percentuais mudam levemente em relação à v1.3.0 (geodésico → plano UTM).
- A tabela/CSV ganham a coluna `Fuso UTM` (posição 4); scripts que leem o CSV por índice devem ser ajustados.
- A camada de saída passa a usar o CRS do projeto.

## 🎨 Requisitos & Compatibilidade

- **QGIS:** 3.16+ | **Python:** 3.12+ | **Dependências raster:** `rasterio`, `shapely` (instalação assistida).

## 📦 Instalação via ZIP

1. QGIS → *Complementos* → *Gerenciar e Instalar Complementos* → *Instalar a partir do ZIP*.
2. Selecione `geointerseq_v1.4.0.zip` (pasta `plugins_zip/`).
3. Clique em *Instalar Complemento* e ative o GeoInterseQ.

**ZIP gerado:** `c:\Python\QGIS Plugins\plugins_zip\geointerseq_v1.4.0.zip`
