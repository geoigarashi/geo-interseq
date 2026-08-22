# KML Merger v1.0.0 — Release Notes

**Data:** 24 de março de 2026
**Plugin:** KML Merger para QGIS 3.16+
**Autor:** Clayton Igarashi

---

## 🎉 Primeira Release — Initial Commit

### ✨ Funcionalidades principais

- ✅ Mescla múltiplos arquivos KML em um único GeoPackage (.gpkg) ou Shapefile (.shp)
- ✅ Processamento paralelo com ThreadPoolExecutor (utiliza todos os núcleos disponíveis)
- ✅ Suporte a arquivos ZIP com extração automática
- ✅ Cálculo de área geodésica em hectares (elipsoide GRS80, EPSG:4674)
- ✅ Extração de propriedades a partir do nome dos arquivos (regex)
- ✅ Log colorido em tempo real com progresso [X/Y]
- ✅ Tema escuro VSCode-like no log
- ✅ Persistência de configurações entre sessões (QSettings)
- ✅ Carregamento automático da camada no QGIS
- ✅ Integração perfeita com QGIS (menu, toolbar, ícone)
- ✅ Cancelamento gracioso com kill robusto (Windows)

### 🏗️ Arquitetura

**Padrão:** Baseado no plugin GeoPipe
**Threading:** QgsTask (thread-safe) + subprocess.Popen
**Parâmetros:** Variáveis de ambiente (KMLM_*)
**Log:** Real-time parsing com regex `[X/Y]`

### 📦 Estrutura do ZIP

```
kml_merger/
├── __init__.py
├── metadata.txt
├── kml_merger_plugin.py
├── kml_merger_dialog.py
├── icon.png
├── README.md
├── .gitignore
└── scripts/
    └── merge_kml.py
```

### 🚀 Instalação

1. **Extraia o ZIP** para qualquer localização temporária
2. **Copie a pasta** `kml_merger` para:
   ```
   %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\
   ```
   Ou crie um symlink:
   ```bash
   mklink /J "%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\kml_merger" "C:\caminho\para\kml_merger"
   ```
3. **Reinicie o QGIS**
4. **Habilite o plugin**: Plugins → Instalar e Gerenciar → Instalados → KML Merger ✓

### 📋 Requisitos

- **QGIS** ≥ 3.16
- **Python** ≥ 3.7 (via OSGeo4W)
- Bibliotecas: `fiona`, `pyproj`

### 🧪 Testes realizados

- ✅ Processamento com 5000+ arquivos KML
- ✅ ZIP com estrutura recursiva de pastas
- ✅ Cancelamento em background
- ✅ Persistência de campos entre sessões
- ✅ Carregamento automático de camada
- ✅ Cálculo de área geodésica (GRS80)
- ✅ Thread-safety (race condition no print — corrigida)
- ✅ Log colorido com progresso [X/Y]

### 🐛 Bugs corrigidos

- **Race condition no print:** Múltiplas threads imprimindo simultaneamente causava linhas concatenadas
  - **Solução:** Mover `print()` dentro do `with lock:`

### 🎨 Visual do Log

- Fundo escuro: `#1e1e1e` (VSCode)
- Erro/Falha: Vermelho `#f44747`
- Aviso: Amarelo `#ffcc00`
- Progresso `[X/Y]`: Azul claro `#9cdcfe`
- Sucesso: Verde-água `#4ec9b0`
- Auto-scroll: `moveCursor(End)` a cada linha

### 📄 Commit

```
Commit: 34200fb
Message: feat: Initial commit - KML Merger plugin for QGIS
Files: 8
Linhas: 1308 insertions
```

### 📚 Documentação

Incluída no ZIP:
- **README.md**: Guia completo de uso e instalação
- **metadata.txt**: Metadados QGIS (nome, versão, autor, tags)

### 🔄 Próximas versões (roadmap)

- [ ] Suporte a outros formatos (GML, GeoJSON)
- [ ] UI para customização de nomes de coluna
- [ ] Validação de geometrias antes de salvar
- [ ] Export para BD (PostGIS)
- [ ] Integração com GDAL/OGR diretamente

### 📝 Notas

Este plugin foi desenvolvido como parte do projeto InfoGEO v2.

**Autor:** Clayton Igarashi
**Email:** geoigarashi@gmail.com

---

## 🆘 Suporte

Em caso de problemas:

1. Verifique se `fiona` e `pyproj` estão instalados
2. Consulte o log do plugin (Plugins → Instalar e Gerenciar → KML Merger → diálogo)
3. Reporte issues no repositório (se disponível)

---

**Versão:** 1.0.0
**Status:** Stable ✅
