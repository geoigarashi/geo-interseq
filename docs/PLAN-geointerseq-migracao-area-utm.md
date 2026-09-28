# PLAN: Migração do Cálculo de Área para Projeção Métrica Plana UTM/SIRGAS 2000 no GeoInterseQ

## Contexto e Diagnóstico

O plugin **GeoInterseQ** (atualmente na v1.3.0) calcula a sobreposição espacial entre uma camada base e camadas analisadas (vetoriais e rasters).

### Modelo Vigente (v1.3.0)
No código atual ([geo_interseq.py](file:///c:/Python/QGIS%20Plugins/GeoInterseQ/geo_interseq.py)):
1. **Espaço Angular:** Todas as geometrias da camada base e das camadas analisadas são reprojetadas para coordenadas geográficas `EPSG:4326` (graus decimais).
2. **Motor de Interseção (GEOS):** As operações booleanas de corte e sobreposição (`g2.intersection(base_union)` e `combine()`) são executadas no espaço euclidiano 2D pelo GEOS, tratando longitude e latitude como eixos ortogonais planos.
3. **Medição Geodésica:** A área do polígono resultante da interseção é calculada via `QgsDistanceArea` com o elipsoide do projeto (padrão WGS84), equivalente à expressão `$area` da Calculadora de Campos do QGIS.

### Limitações e Problemas Identificados
1. **Divergência com Laudos e Memoriais:** Técnicos agrícolas, engenheiros, laudos do Proagro/BACEN e peças cartorárias utilizam rotineiramente projeções métricas locais (SIRGAS 2000 UTM) e áreas euclidianas planas (`area($geometry)` ou CAD). Devido ao fator de escala da projeção UTM ($k$), a área geodésica elipsoidal diverge da área plana UTM entre **0,08%** (no meridiano central) e mais de **0,30%** (nas bordas do fuso), gerando contestações em auditorias.
2. **Deformação de Arestas no GEOS:** Como $1^\circ$ de longitude equivale a $111 \text{ km} \times \cos(\text{lat})$, operar a interseção do GEOS em graus decimais introduz assimetria angular nos segmentos e ruídos numéricos de ponto flutuante em geometrias complexas.
3. **Inconsistência de Borda no Modo Pareado:** O cálculo geodésico pós-interseção angular ocasionalmente gerava áreas de interseção ligeiramente superiores à menor gleba do par em frações decimais, exigindo alertas artificiais de consistência.

---

## Decisões Alinhadas no Grill-Me / Brainstorm

1. **Migração para Projeção Métrica Plana Dinâmica:**
   - O cálculo das interseções e a extração de áreas migrarão integralmente para **UTM / SIRGAS 2000**.
   - As operações booleanas do GEOS rodarão em coordenadas ortogonais métricas reais (metros).
2. **Método de Extração de Área:**
   - Cartesiano euclidiano puro (`geom.area()`), garantindo **100% de paridade** com a expressão `area($geometry)` do QGIS, memoriais descritivos em UTM e softwares de topografia/CAD.
3. **Determinação Dinâmica do Fuso UTM:**
   - Em vez de um fuso fixo para o projeto inteiro, o fuso UTM/SIRGAS 2000 ideal será determinado **dinamicamente por par/gleba** a partir do centróide das geometrias envolvidas.
   - Suporte a fusos do Brasil sob **SIRGAS 2000** (EPSG 31978 a 31985 para hemisfério Sul, e 31972 a 31976 para hemisfério Norte), com fallback transparente para WGS 84 UTM em coordenadas fora do continente.
4. **CRS das Camadas Temporárias de Saída:**
   - As camadas de memória geradas no QGIS adotarão o **CRS do Projeto Ativo (`QgsProject.instance().crs()`)**, reprojetando as geometrias calculadas em UTM para o CRS visual do usuário.
5. **Harmonização com a Análise Vetor × Raster:**
   - Na análise de uso do solo com rasters categóricos, as classes vetorizadas e recortadas com a base serão medidas diretamente na mesma projeção métrica UTM local (`qgs_geom_utm.area()`).
6. **Rastreabilidade e Auditoria:**
   - Adição da coluna `Fuso UTM` (`fuso_utm` / ex: `SIRGAS 2000 / UTM 22S`) na tabela de resultados da interface, nos atributos das camadas geradas e no arquivo CSV exportado.
7. **Detecção e Sinalização de Polígonos Transfronteiriços (Borda de Fusos UTM):**
   - Caso uma gleba ou feição cruze o meridiano divisor entre dois fusos UTM ($\text{lon} \equiv 0 \pmod 6$, como o meridiano $-54^\circ$ entre os fusos 21S e 22S), o polígono **não será fatiado** (mantendo integridade topológica e paridade 1:1 de atributos).
   - O cálculo é unificado no fuso do seu centróide e o sistema sinaliza explicitamente a condição transfronteiriça no atributo `fuso_utm` (ex: `SIRGAS 2000 / 22S (borda)`) e no `QgsMessageLog`.

---

## Especificação Técnica das Alterações

### 1. Novo Método Auxiliar: `_get_optimal_utm_crs`
Local: [geo_interseq.py](file:///c:/Python/QGIS%20Plugins/GeoInterseQ/geo_interseq.py)

```python
def _get_optimal_utm_crs(
    self, geom: QgsGeometry, ctx: QgsCoordinateTransformContext, source_crs: QgsCoordinateReferenceSystem
) -> tuple[QgsCoordinateReferenceSystem, str, bool]:
    """Calcula o CRS UTM/SIRGAS 2000 ótimo para a geometria a partir do seu centróide geográfico e detecta cruzamento de fusos.

    Args:
        geom: Geometria de referência.
        ctx: Contexto de transformação de coordenadas do QGIS.
        source_crs: CRS de entrada da geometria.

    Returns:
        tuple[QgsCoordinateReferenceSystem, str, bool]: 
            - Instância do CRS projetado;
            - Rótulo formatado (ex: 'SIRGAS 2000 / UTM 22S' ou 'SIRGAS 2000 / UTM 22S (borda)');
            - Flag booleana indicando se a geometria é transfronteiriça (cruza múltiplos fusos).
    """
```
- Reprojeta temporariamente a geometria e seu centróide para `EPSG:4326`.
- Determina a zona UTM pelo centróide: `zone = int(math.floor((lon_c + 180.0) / 6.0)) + 1`.
- **Detecção de Cruzamento de Fusos (Transfronteiriço):**
  - Avalia a extensão em longitude do bounding box da geometria:
    `zone_min = int(math.floor((bbox.xMinimum() + 180.0) / 6.0)) + 1`
    `zone_max = int(math.floor((bbox.xMaximum() + 180.0) / 6.0)) + 1`
  - Se `zone_min != zone_max`: `is_cross_zone = True`.
  - Sufixo no rótulo: `label = f"{base_label} (borda)"` se `is_cross_zone` for True.
  - Registro de Log:
    ```python
    QgsMessageLog.logMessage(
        f'Gleba transfronteiriça detectada entre os fusos UTM {zone_min} e {zone_max}. '
        f'Cálculo unificado no Fuso {zone} pelo centróide.',
        'GeoInterseQ', Qgis.Info,
    )
    ```
- Para o Brasil / América do Sul:
  - Sul (`lat < 0`): `epsg = 31980 + zone` (ex: 31981 para 21S, 31982 para 22S).
  - Norte (`lat >= 0`): `epsg = 31960 + zone` (ou tabela 31972-31976).
  - Fallback global: `epsg = (32700 + zone)` se Sul senão `(32600 + zone)`.
- Retorna `(QgsCoordinateReferenceSystem(f'EPSG:{epsg}'), label, is_cross_zone)`.

---

### 2. Refatoração do Modo Vetor × Vetor Pareado (`_process_vector_layer_paired`)
Local: [geo_interseq.py:1058-1214](file:///c:/Python/QGIS%20Plugins/GeoInterseQ/geo_interseq.py#L1058-L1214)

1. Para cada `key_val` (`id_par`):
   - Unir geometrias da base e da analisada em seu CRS nativo ou EPSG:4326.
   - Determinar o CRS UTM ótimo para o par usando o centróide conjunto (`geom_base.combine(geom_overlay)`).
   - Criar transformadores:
     - `tr_to_utm = QgsCoordinateTransform(src_crs, crs_utm, ctx)`
     - `tr_to_out = QgsCoordinateTransform(crs_utm, crs_out_project, ctx)`
   - Reprojetar `geom_base` e `geom_overlay` para `crs_utm` e validar (`makeValid()`).
2. Medição em metros planos:
   - `area_base_m2 = geom_base.area()`
   - `area_overlay_m2 = geom_overlay.area()`
3. Interseção em metros planos:
   - `inter_geom_utm = geom_base.intersection(geom_overlay).makeValid()`
   - `inter_area_m2 = inter_geom_utm.area() if inter_geom_utm and not inter_geom_utm.isEmpty() else 0.0`
4. Em metros cartesianos, a propriedade geométrica $A(A \cap B) \le \min(A(A), A(B))$ é estritamente satisfeita pelo GEOS (tolerância de floating point $\approx 10^{-6}$).
5. Reprojetar `inter_geom_utm` para o CRS do projeto (`tr_to_out`) ao gravar na camada em memória.
6. Gravar `fuso_utm_label` na tabela de resultados e nos atributos da feição de saída.

---

### 3. Refatoração do Modo Vetor × Vetor Convencional (`_process_vector_layer`)
Local: [geo_interseq.py:979-1057](file:///c:/Python/QGIS%20Plugins/GeoInterseQ/geo_interseq.py#L979-L1057)

1. Para cada feição analisada que intersecta o bounding box da base:
   - Determinar o CRS UTM local ótimo da feição/interseção.
   - Reprojetar a feição analisada e a `base_union` para esse CRS UTM métrico.
   - Medir `feat_area_m2 = feat_geom_utm.area()`.
   - Executar `inter_geom_utm = feat_geom_utm.intersection(base_union_utm).makeValid()`.
   - Medir `inter_area_m2 = inter_geom_utm.area()`.
   - Se `inter_area_m2 < 1.0` $m^2$: descartar ruído.
   - Reprojetar `inter_geom_utm` para o CRS do projeto antes de inserir na `out_layer`.
   - Inserir na tabela e camada com o rótulo do fuso UTM.

---

### 4. Refatoração do Modo Vetor × Raster (`_process_raster_layer`)
Local: [geo_interseq.py:1215-1570](file:///c:/Python/QGIS%20Plugins/GeoInterseQ/geo_interseq.py#L1215-L1570)

1. Determinar o CRS UTM ótimo para a camada base.
2. Reprojetar a geometria da base para esse CRS UTM (`base_utm`) e calcular `base_area_m2_ref = base_utm.area()`.
3. Ao vetorizar as classes com `rio_shapes` e recortar com a base via Shapely:
   - Converter o polígono recortado resultante para `QgsGeometry`.
   - Reprojetar a geometria da classe para o mesmo CRS UTM da base.
   - Medir a área de cada classe com `class_geom_utm.area()`.
4. Reprojetar as geometrias de classe para o CRS do projeto para exibição visual na camada temporária `raster_out`.
5. Preencher o atributo `fuso_utm` em cada classe na tabela e na camada.

---

### 5. Atualização da Interface, Camadas e CSV
Local: [geo_interseq.py](file:///c:/Python/QGIS%20Plugins/GeoInterseQ/geo_interseq.py)

1. **Tabela da Interface (`self.table`):**
   - Cabeçalhos passam de 5 para 6 colunas:
     `['Tipo', 'Camada', 'Classe / Rótulo', 'Fuso UTM', f'Área ({self.cmb_unit.currentText()})', '% Sobreposição']`
2. **Método `_insert_result_row_with_class`:**
   - Novo parâmetro: `fuso_utm: str = ''`.
   - Preenchimento da coluna 3 com o fuso e tooltip informativo.
3. **Camada em Memória (`_make_out_layer`):**
   - CRS configurado com `QgsProject.instance().crs()`.
   - Atributos:
     `type` (string), `layer` (string), `class` (string), `fuso_utm` (string), `area_m2` (double), `area_ha` (double), `percent` (double).
4. **Exportação CSV (`export_csv`):**
   - Mantém o delimitador `;` e codificação `utf-8-sig`.
   - Exporta automaticamente a nova coluna `Fuso UTM`.

---

### 6. Atualização de Metadados e Documentação
1. **`metadata.txt`:**
   - Incrementar versão: `1.3.0` $\rightarrow$ `1.4.0`.
   - Atualizar changelog destacando a migração do cálculo geodésico para projeção métrica cartesiana UTM/SIRGAS 2000 dinâmica e inclusão da rastreabilidade de fuso.
2. **`README.md` e `documento.md`:**
   - Atualizar a seção técnica detalhando o novo algoritmo de fuso dinâmico e paridade com `area($geometry)`.
3. **Release Notes:**
   - Criar `docs/RELEASE_v1.4.0.md` registrando a justificativa técnica para auditorias de crédito rural.

---

## Plano de Testes e Validação

1. **Teste de Paridade Cartesiana:**
   - Comparar o resultado do GeoInterseQ v1.4.0 com a Calculadora de Campos do QGIS usando a expressão `area($geometry)` para uma camada em SIRGAS 2000 / UTM.
   - **Critério de Sucesso:** Diferença absoluta $< 0,001 \text{ m}^2$ (erro estritamente de ponto flutuante).
2. **Teste de Paridade com Laudos:**
   - Confrontar glebas de teste de Contrato e RCP em diferentes fusos (ex: Fuso 21S e Fuso 22S).
   - **Critério de Sucesso:** O fuso identificado dinamicamente corresponde ao centróide local da gleba e a área calculada não sofre distorções de fusos adjacentes.
3. **Teste de Consistência Topológica:**
   - Verificar se para qualquer par testado, $\text{área de interseção} \le \min(\text{área base}, \text{área overlay})$.
   - **Critério de Sucesso:** Zero avisos de extrapolação geométrica.
4. **Teste de Análise Raster:**
   - Executar análise com raster MapBiomas / uso do solo.
   - **Critério de Sucesso:** Soma das áreas das classes igual a 100% da área da gleba base em UTM.
5. **Teste de Rastreabilidade e Exportação:**
   - Exportar o CSV e verificar presença da coluna `Fuso UTM` com codificação correta no Excel.
6. **Teste de Polígono Transfronteiriço (Divisa de Fusos UTM):**
   - Executar análise com gleba de teste que atravesse o meridiano divisor (ex: $-54^\circ$, entre os fusos 21S e 22S).
   - **Critério de Sucesso:** Detecção automática do cruzamento, exibição de `(borda)` na coluna `Fuso UTM`, registro informativo no `QgsMessageLog` e integridade contínua do polígono sem fracionamento espúrio.

---

## Matriz de Riscos e Mitigações

| Risco | Impacto | Mitigação |
| :--- | :--- | :--- |
| Glebas muito extensas que cruzam a fronteira de dois fusos UTM | Baixo | O centróide define o fuso unificado contínuo (PROJ estende analiticamente as coordenadas sem deformações abruptas), com registro automático de `(borda)` no atributo e log |
| Camadas de entrada sem CRS definido ou inválido | Alto | O plugin manterá validação estrita com diálogo de erro caso o CRS da camada seja inválido |
| Coordenadas fora do Brasil (usuários internacionais) | Baixo | Fallback automático para WGS 84 / UTM zonas 1 a 60 N/S |
| Quebra de scripts externos dependentes dos nomes de colunas | Baixo | A coluna `fuso_utm` é adicionada preservando a integridade das colunas numéricas `area_m2`, `area_ha` e `percent` |
