# Instruções de Correção Técnica para LLM — Alinhamento de Grade Raster no Plugin QGIS `GeoInterseQ`

## 1. Contexto e Objetivo
Ao executar a interseção entre uma camada vetorial base (polígono de imóvel) e uma camada matricial (GeoTIFF de uso e cobertura do solo) no plugin **`GeoInterseQ`** (`C:\Python\QGIS Plugins\GeoInterseQ\geo_interseq.py`), as áreas calculadas por classe apresentam divergências métricas e um deslocamento espacial sub-pixel (de até 1 pixel em X e Y, equivalente a `~10 m` em rasters de 10m) em relação ao *Ground Truth* oficial do GDAL / `rasterio.mask.mask` e da plataforma `infogeo-valoracao`.

**Objetivo:** Corrigir o cálculo da janela de leitura do raster (`rasterio.windows.Window`) em `geo_interseq.py` para ancorar os limites (`col_off`, `row_off`, `width`, `height`) estritamente nos índices inteiros da grade nativa de pixels do GeoTIFF, eliminando a translação sub-pixel da transformação afim e a reamostragem implícita do GDAL.

---

## 2. Diagnóstico de Causa Raiz (*Root Cause Analysis*)

Em `C:\Python\QGIS Plugins\GeoInterseQ\geo_interseq.py` (linhas `1390–1420`), o recorte da janela do raster é realizado atualmente da seguinte forma:

```python
_minx, _miny, _maxx, _maxy = shapely_geom.bounds
with rasterio.open(raster_path) as _src_rio:
    _window = rasterio.windows.from_bounds(
        _minx, _miny, _maxx, _maxy,
        transform=_src_rio.transform
    )
    src_window = _window.crop(height=_src_rio.height, width=_src_rio.width)
    # ...
    data_masked = _src_rio.read(1, window=src_window, masked=True)
    window_affine = rasterio.windows.transform(src_window, _src_rio.transform)
```

### Por que esse código gera erro posicional e de área?
1. **`rasterio.windows.from_bounds` retorna offsets em ponto flutuante (`float`):**
   Os atributos `_window.col_off`, `_window.row_off`, `_window.width` e `_window.height` são números fracionários contínuos correspondentes às coordenadas exatas do *bounding box* do polígono (ex.: `col_off = 341915.9305`, `row_off = 217645.4803`, `width = 702.8260`, `height = 697.0494`), e **não** aos cantos inteiros dos pixels do GeoTIFF.
2. **Distorção 1 — Translação da Grade em `rasterio.windows.transform`:**
   Quando `rasterio.windows.transform(src_window, _src_rio.transform)` recebe um `src_window` com `col_off` e `row_off` fracionários, a origem `(c, f)` da nova matriz afim (`window_affine`) é posicionada sobre o *bounding box* do vetor em vez do canto superior-esquerdo real do pixel `[int(row_off), int(col_off)]` do GeoTIFF. Isso desloca fisicamente todos os polígonos vetorizados por `rasterio.features.shapes` em até `0,99` pixel na horizontal e na vertical.
3. **Distorção 2 — Reamostragem Silenciosa no `GDALRasterIOEx` (`_src_rio.read`):**
   Quando `_src_rio.read(1, window=src_window)` recebe `col_off`, `row_off`, `width` e `height` em ponto flutuante, o GDAL aloca um buffer inteiro de dimensões `(round(height), round(width))` e executa reamostragem *nearest-neighbor* sobre a janela fracionária, alterando os valores de milhares de pixels ao longo das bordas internas de classes.
4. **Distorção 3 — Ausência de Buffer de 1 Pixel na Borda do *Bounding Box*:**
   Sem expandir os limites de busca em 1 pixel antes de arredondar para inteiros (`math.floor` para offsets iniciais e `math.ceil` para offsets finais), pixels limítrofes tocados pelo vértice extremo do polígono podem ser truncados na borda direita/inferior.

---

## 3. Especificação da Correção Cirúrgica

### Arquivo Alvo
* `C:\Python\QGIS Plugins\GeoInterseQ\geo_interseq.py` (linhas `1390–1420`)

### O que alterar
1. Aplicar um buffer de segurança de `1 pixel` (`max(abs(_src_rio.transform.a), abs(_src_rio.transform.e))`) sobre os limites (`_minx, _miny, _maxx, _maxy`) para garantir cobertura integral das bordas.
2. Converter a janela retornada por `rasterio.windows.from_bounds` para índices **estritamente inteiros** usando `math.floor` para `col_off`/`row_off` e `math.ceil` para o limite oposto (`col_off + width` e `row_off + height`) antes de aplicar `.crop(...)`.

### Código Antes (Com Bug)
```python
        _minx, _miny, _maxx, _maxy = shapely_geom.bounds
        with rasterio.open(raster_path) as _src_rio:
            _window = rasterio.windows.from_bounds(
                _minx, _miny, _maxx, _maxy,
                transform=_src_rio.transform
            )
            src_window = _window.crop(height=_src_rio.height, width=_src_rio.width)
```

### Código Depois (Corrigido — Paridade 100% com Grade Nativa do GeoTIFF)
```python
        import math
        _minx, _miny, _maxx, _maxy = shapely_geom.bounds
        with rasterio.open(raster_path) as _src_rio:
            _res_x: float = abs(_src_rio.transform.a)
            _res_y: float = abs(_src_rio.transform.e)
            _buf: float = max(_res_x, _res_y)

            _raw_window = rasterio.windows.from_bounds(
                _minx - _buf,
                _miny - _buf,
                _maxx + _buf,
                _maxy + _buf,
                transform=_src_rio.transform,
            )
            _col_off: int = math.floor(_raw_window.col_off)
            _row_off: int = math.floor(_raw_window.row_off)
            _width: int = math.ceil(_raw_window.col_off + _raw_window.width) - _col_off
            _height: int = math.ceil(_raw_window.row_off + _raw_window.height) - _row_off

            _int_window = rasterio.windows.Window(_col_off, _row_off, _width, _height)
            src_window = _int_window.crop(height=_src_rio.height, width=_src_rio.width)
```

---

## 4. Critérios de Verificação Pós-Correção

Após aplicar a alteração acima em `C:\Python\QGIS Plugins\GeoInterseQ\geo_interseq.py`:
1. **Invariante de Alinhamento Matricial:**
   * `src_window.col_off`, `src_window.row_off`, `src_window.width` e `src_window.height` devem ser números inteiros exatos.
   * A coordenada `window_affine * (0, 0)` deve coincidir exatamente (`erro = 0,00 m`) com `_src_rio.transform * (src_window.col_off, src_window.row_off)`.
2. **Paridade com `rasterio.mask.mask` (*Ground Truth*):**
   * As áreas brutas em hectares calculadas por classe pelo `GeoInterseQ` (via vetorização GEOS + projeção UTM SIRGAS 2000) devem coincidir até a 4ª casa decimal (`0,0000 ha` de diferença) com o resultado obtido via `rasterio.mask.mask(src, [shapely_geom], crop=True, all_touched=True)`.
3. **Inspeção Visual no QGIS (Zoom `1:1.000`):**
   * As feições vetoriais geradas na camada de saída do `GeoInterseQ` devem encaixar perfeitamente sobre os contornos dos pixels do raster original no canvas do QGIS, sem deslocamento lateral ou vertical.
