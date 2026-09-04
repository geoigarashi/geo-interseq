# GeoInterseQ

<p align="center">
  <img src="icon.png" alt="Ícone GeoInterseQ" height="120" style="vertical-align: middle; margin-right: 30px;">
  <img src="Logo-GEO-HQ.svg" alt="Logotipo Plataforma Geo e Inovação" height="120" style="vertical-align: middle;">
</p>

**Versão 1.3.0** | **Autores:** Plat. Geo e Inovação

---

## Descrição

Plugin para o QGIS desenvolvido para calcular a área de interseção e o percentual de sobreposição entre uma camada base (de polígonos vetoriais) e múltiplas camadas analisadas (que podem ser tanto vetoriais quanto raster).

### Principais Funcionalidades
* **Análise vetor × vetor:** cruzamento espacial por feição, com campo de rótulo configurável.
* **Análise vetor × raster:** cruzamento espacial por classe (raster categórico inteiro), garantindo paridade numérica com a metodologia adotada pelo InfoGEO e robustez total na reprojeção automática via `QgsCoordinateTransform`.
* **Flexibilidade de Escopo:** dois modos de cálculo percentual disponíveis:
  * `% da feição analisada` (ex: quanto da gleba intersecta o imóvel).
  * `% da camada base` (ex: quanto do imóvel é coberto pela feição analisada).
* **Camadas de Interseção:** geração de camadas temporárias de interseção com a simbologia original do raster aplicada automaticamente.
* **Exportação de Resultados:** exportação direta dos dados calculados em formato CSV (separador `;`, codificação UTF-8 com BOM para total compatibilidade com Excel).
* **Assistente de Dependências com 1 Clique:** instalação automatizada das bibliotecas `rasterio` e `shapely` no perfil do usuário (`--user`), dispensando privilégios de Administrador.

---

## Requisitos

1. **QGIS >= 3.16** (inclui nativamente GDAL/OGR, numpy e PyQt5).
2. **Para análise de camadas RASTER:**
   * `rasterio`
   * `shapely`

> [!TIP]
> **Instalação Automática com 1 Clique:**
> Ao abrir o GeoInterseQ ou ao adicionar uma camada raster pela primeira vez, o plugin detectará se as bibliotecas estão presentes e oferecerá a instalação automática com um clique. Não é necessário abrir o terminal ou ter privilégios de Administrador.

---

## Instalação de Dependências

### Opção A — Assistente Integrado do Plugin (Recomendado)
1. Abra o **GeoInterseQ** no QGIS.
2. Se faltarem bibliotecas, confirme o diálogo clicando em **Sim** ou abra o assistente integrado.
3. Clique em **Instalar Dependências** e aguarde a barra de progresso.
4. As bibliotecas são instaladas com `--user` e vinculadas à sessão em tempo real.

### Opção B — Instalação Manual via OSGeo4W Shell
1. Abra o **OSGeo4W Shell** (como Administrador ou usuário comum com `--user`).
2. Execute o comando:
   ```bash
   pip install --user rasterio shapely
   ```

### Opção C — Console Python do QGIS
1. No menu principal do QGIS, acesse **Plugins > Console Python**.
2. Execute o seguinte trecho de código:
   ```python
   import subprocess, sys
   subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'rasterio', 'shapely'])
   ```

---

## Instalação do Plugin

1. No QGIS, acesse: **Plugins > Gerenciar e Instalar Plugins > Instalar a partir de arquivo ZIP**.
2. Selecione o arquivo `geointerseq_v1.3.0.zip` gerado em `plugins_zip/`.


---

## Suporte e Manutenção

* **Equipe de Desenvolvimento:** Plat. Geo e Inovação
