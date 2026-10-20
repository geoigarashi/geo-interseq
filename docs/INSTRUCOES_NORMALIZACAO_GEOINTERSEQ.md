# Instruções de Correção Técnica para LLM — Paridade de Normalização e Fechamento de Área no Plugin QGIS `GeoInterseQ`

## 1. Contexto e Objetivo
Após a correção do alinhamento da janela matricial (`align_raster_window`), o cálculo bruto de áreas por classe no plugin **`GeoInterseQ`** (`C:\Python\QGIS Plugins\GeoInterseQ\geo_interseq.py`) atingiu paridade geométrica exata (`0,0000 ha` de diferença bruta) com o motor da plataforma **`infogeo-valoracao`** (`c:\Python\infogeo-valoracao\server\valoracao_core.py`).

Todavia, resta uma diferença residual na 3ª/4ª casa decimal (da ordem de `~1,5 ppm` ou `0,00015%`, ex.: `0,0041 ha` em um polígono de `2.732,6054 ha`) entre o CSV exportado pelo `GeoInterseQ` e o Laudo PDF do `infogeo-valoracao`.

**Objetivo:** Igualar a regra de normalização (fechamento contábil da área em `100%` da área plana do polígono base) em `C:\Python\QGIS Plugins\GeoInterseQ\geo_interseq.py` à regra utilizada em `c:\Python\infogeo-valoracao\server\valoracao_core.py`, garantindo paridade absoluta até a 4ª casa decimal (`0,0001 ha`) entre ambos os sistemas.

---

## 2. Diagnóstico de Causa Raiz (*Root Cause Analysis*)

### 2.1. Fenômeno Cartográfico: Densificação de Vértices na Reprojeção (`EPSG:4326 → UTM`)
1. A área de referência da camada base (`base_area_m2_ref`) é calculada projetando o polígono original diretamente para o fuso UTM correspondente (`SIRGAS 2000 / UTM`). Seus segmentos retos longos são projetados a partir de seus vértices originais.
2. Já no processamento do raster (`EPSG:4326`), a máscara de pixels é vetorizada (`rasterio.features.shapes`) e recortada contra o polígono base ainda no CRS geográfico do raster (`merged.intersection(shapely_geom)`).
3. Esse recorte fatiado insere milhares de vértices intermediários a cada `~10 m` (resolução do pixel) ao longo das bordas do polígono. Quando cada fragmento é projetado de `EPSG:4326` para UTM (`raster_cache.project_to_utm`), a curvatura da projeção Transversa de Mercator sobre os segmentos densificados gera uma soma total (`sum(areas_por_classe_m2.values())`) ligeiramente inferior à área do polígono original (diferença típica de `0,0001%` a `0,0002%`).

### 2.2. Divergência na Condição de Normalização
Em `c:\Python\infogeo-valoracao\server\valoracao_core.py` (linhas `936–944`), a normalização proporcional é aplicada bilateralmente sempre que a diferença residual de discretização/densificação é inferior a `0,5%` (`discretization_ratio <= 0.005`) ou quando a soma das classes excede a área base:

```python
        area_classes_total_ha = float(sum(areas_por_classe_ha.values()))
        if base_area_ha > 0 and area_classes_total_ha > 0:
            discretization_ratio = abs(base_area_ha - area_classes_total_ha) / base_area_ha
            if discretization_ratio <= 0.005 or area_classes_total_ha > base_area_ha:
                fator = base_area_ha / area_classes_total_ha
                areas_por_classe_ha = {k: v * fator for k, v in areas_por_classe_ha.items()}
                area_classes_total_ha = float(sum(areas_por_classe_ha.values()))
```

Já em `C:\Python\QGIS Plugins\GeoInterseQ\geo_interseq.py` (linhas `1546–1551`), a condição atual é **unilateral** (só normaliza quando a soma das classes é maior que `base_area_m2_ref * 1.0001`):

```python
        # Ajuste para evitar que aproximações numéricas na discretização excedam a área de referência do imóvel
        area_classes_total_m2: float = sum(areas_por_classe_m2.values())
        if area_classes_total_m2 > base_area_m2_ref * 1.0001:
            fator: float = base_area_m2_ref / area_classes_total_m2
            areas_por_classe_m2 = {k: v * fator for k, v in areas_por_classe_m2.items()}
            area_classes_total_m2 = sum(areas_por_classe_m2.values())
```

Como a soma dos fragmentos densificados fica `~0,00015%` **abaixo** de `base_area_m2_ref`, o `if` do `GeoInterseQ` não é acionado e a soma exportada no CSV não fecha exatamente com a área plana da camada base.

---

## 3. Especificação da Correção Cirúrgica

### Arquivo Alvo
* `C:\Python\QGIS Plugins\GeoInterseQ\geo_interseq.py` (linhas `1546–1552`)

### Código Antes
```python
        # Ajuste para evitar que aproximações numéricas na discretização excedam a área de referência do imóvel
        area_classes_total_m2: float = sum(areas_por_classe_m2.values())
        if area_classes_total_m2 > base_area_m2_ref * 1.0001:
            fator: float = base_area_m2_ref / area_classes_total_m2
            areas_por_classe_m2 = {k: v * fator for k, v in areas_por_classe_m2.items()}
            area_classes_total_m2 = sum(areas_por_classe_m2.values())
```

### Código Depois (Paridade Estrita com `infogeo-valoracao`)
```python
        # Fechamento contábil de área (paridade com infogeo-valoracao):
        # Quando o raster cobre integralmente o polígono (resíduo de densificação UTM <= 0,5%)
        # ou quando a soma excede a área base, normaliza as classes para fechar 100% da área de referência.
        area_classes_total_m2: float = float(sum(areas_por_classe_m2.values()))
        if base_area_m2_ref > 0.0 and area_classes_total_m2 > 0.0:
            discretization_ratio: float = abs(base_area_m2_ref - area_classes_total_m2) / base_area_m2_ref
            if discretization_ratio <= 0.005 or area_classes_total_m2 > base_area_m2_ref:
                fator: float = base_area_m2_ref / area_classes_total_m2
                areas_por_classe_m2 = {k: v * fator for k, v in areas_por_classe_m2.items()}
                area_classes_total_m2 = float(sum(areas_por_classe_m2.values()))
```

---

## 4. Sincronização com o Perfil Ativo do QGIS
Após editar `C:\Python\QGIS Plugins\GeoInterseQ\geo_interseq.py`, lembre-se de copiar o arquivo atualizado para o diretório ativo de plugins do QGIS antes de testar na interface:

```powershell
Copy-Item "C:\Python\QGIS Plugins\GeoInterseQ\geo_interseq.py" "$env:APPDATA\QGIS\QGIS3\profiles\default\python\plugins\GeoInterseQ\geo_interseq.py" -Force
```

---

## 5. Critérios de Verificação Pós-Correção
1. **Fechamento Exato de Área (`100,0000%`):** A soma das áreas exportadas em hectares no CSV do `GeoInterseQ` deve coincidir até a 4ª casa decimal com a área plana UTM do polígono base.
2. **Paridade Absoluta com `infogeo-valoracao`:** Todas as classes devem apresentar `0,0000 ha` de diferença entre o CSV exportado pelo `GeoInterseQ` e o Laudo PDF emitido pelo `infogeo-valoracao`.
