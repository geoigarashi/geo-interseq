# 🌐 GeoInterseQ — v1.2.1

**Data de Lançamento:** 02 de setembro de 2026

---

## ✨ Destaques da Versão

### 🎯 Correção Crítica de Reprojeção de CRS em Rasters
* **Reprojeção Canônica via QGIS (`QgsCoordinateTransform`):** Substituição da lógica frágil de inferência de código EPSG via strings (`authid().split(':')[-1]`) e chamadas a `pyproj.Transformer` pela engine nativa de transformação de coordenadas do QGIS (`QgsCoordinateTransform(base_source_crs, raster_crs, ctx)`).
* **Compatibilidade com Datums e Shapefiles Legados/ESRI:** Corrige falha silenciosa onde camadas com arquivos `.prj` sem autoridade EPSG explícita (ex: Shapefiles com WKT puro de SIRGAS 2000 ou SAD69) geravam `src_epsg = None`, impedindo a reprojeção para o CRS do raster e resultando na mensagem indevida: *"O raster não cobre a extensão da camada base"*.
* **Resolução Robusta de CRS de Camadas Raster:** Leitura prioritária de `lyr.crs()` com fallback seguro para `QgsCoordinateReferenceSystem.fromWkt(ds.GetProjection())`.
* **Vetorização e Medição Geodésica 100% Integradas:** A reprojeção das classes raster vetorizadas para o CRS de cálculo (`EPSG:4326`) agora ocorre nativamente em objetos `QgsGeometry`, assegurando paridade elipsoidal absoluta e eliminação de falhas de transformação.

---

## 📋 Resumo de Mudanças

### 🐛 Correções de Bugs (v1.2.1)
- 🛠️ **Fix na reprojeção vetorial da base para o raster:** Feições da base agora são transformadas individualmente via `QgsCoordinateTransform` nativo antes da conversão para geometrias Shapely locais do raster.
- 🛠️ **Remoção de dependência de strings EPSG no pyproj:** Eliminada qualquer suposição de que o CRS contenha código EPSG numérico nos formatos `"EPSG:XXXX"`.
- 🛠️ **Fallback automático e robusto:** Caso uma das fontes vetoriais nativas falhe na transformação pontual, o fallback reconstrói a geometria de forma consistente a partir do `base_union`.
- 🛠️ **Atribuição direta de geometria no out_layer:** A inserção de feições na camada temporária passa a usar `feat.setGeometry(geom_4326)` diretamente, evitando conversões desnecessárias para WKT string.

---

## 🎨 Compatibilidade

- **QGIS:** 3.16+ (testado e homologado no QGIS 3.44.14-Solothurn)
- **Python:** 3.12+ (Type hints modernos, PEP8 e compatível com Ruff)
- **Dependências:** `rasterio`, `shapely`

---

## 📦 Conteúdo do Pacote

```
geointerseq_v1.2.1.zip
└── GeoInterseQ/
    ├── __init__.py          # Inicialização e validação de dependências
    ├── metadata.txt         # Versão 1.2.1 e changelog
    ├── icon.png             # Ícone oficial do plugin
    ├── Logo-GEO-HQ.svg      # Logotipo vetorizado Plataforma Geo
    ├── README.md            # Guia de instalação e requisitos
    └── geo_interseq.py      # Lógica de interface PyQt5 e backend geoespacial
```

---

## 🚀 Como Atualizar

1. Faça o download ou localize o pacote `geointerseq_v1.2.1.zip` no diretório `plugins_zip/`.
2. No menu do QGIS, acesse **Plugins > Gerenciar e Instalar Plugins > Instalar a partir de arquivo ZIP**.
3. Selecione o arquivo e clique em **Instalar Plugin**.
