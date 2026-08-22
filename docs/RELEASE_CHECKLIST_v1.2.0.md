# 📋 Release Checklist — Smart GeoTIFF Exporter v1.2.0

**Data:** 26 de março de 2026
**Status:** ✅ PRONTO PARA LANÇAMENTO

---

## ✅ Verificações Completadas

### 📦 Artefatos de Distribuição
- ✅ **Arquivo .zip gerado:** `smart_geotiff_exporter_v1.2.0.zip`
  - Tamanho: **9.9 KB** (comprimido)
  - Localização: `c:\Python\QGIS Plugins\`
  - Conteúdo: 5 arquivos principais
    - `__init__.py`
    - `metadata.txt` (versão 1.2.0)
    - `smart_geotiff_exporter.py`
    - `smart_geotiff_exporter_dialog.py`
    - `icon.png`
  - Exclusões confirmadas: `.git/`, `docs/`, `CLAUDE.md`, `.vscode/`, `README.md`

### 📄 Documentação de Release
- ✅ **Markdown completo:** `RELEASE_v1.2.0.md`
  - Destaques de features
  - Instruções de instalação
  - Exemplos de uso
  - Compatibilidade documentada

- ✅ **Texto simples para GitHub:** `GITHUB_RELEASE_v1.2.0.txt`
  - Formato adequado para GitHub Releases
  - Listas de funcionalidades e melhorias
  - Links do repositório

### 🎯 Alterações Versionadas
- ✅ **metadata.txt:** Versão atualizada para `1.2.0`
- ✅ **Git tag:** `v1.2.0` criada no repositório
- ✅ **Histórico de commits:**
  - `732b42b` — feat(nodata): Valor NoData configurável
  - `b8f09aa` — merge: integração main
  - `398018a` — chore: menu → Ferramentas Geo
  - `17494d2` — docs: README atualizado
  - `9f133af` — style: ruff format + ruff check --fix

### 🔍 Código & Qualidade
- ✅ **Refatoração de código:** ruff format + ruff check --fix aplicados
- ✅ **Sem bugs críticos:** v1.1.0 foi estável
- ✅ **Compatibilidade testada:** QGIS 3.16+

---

## 📋 Arquivos Gerados

```
c:\Python\QGIS Plugins\
├── smart_geotiff_exporter_v1.2.0.zip          [9.9 KB] ← DISTRIBUIÇÃO
├── smart_geotiff_exporter_v1.2.0.tar.gz       [9.9 KB] (equivalente)
├── RELEASE_v1.2.0.md                          ← Markdown detalhado
├── GITHUB_RELEASE_v1.2.0.txt                  ← GitHub format
└── RELEASE_CHECKLIST_v1.2.0.md                ← Este arquivo
```

---

## 🚀 Próximos Passos para Lançamento

### No GitHub:
1. **Criar Release:**
   - Tag: `v1.2.0`
   - Título: `Smart GeoTIFF Exporter v1.2.0 — NoData Configurável`
   - Descrição: Copiar conteúdo de `GITHUB_RELEASE_v1.2.0.txt`
   - Arquivo: Fazer upload de `smart_geotiff_exporter_v1.2.0.zip`

2. **Atualizar README.md:**
   - Adicionar seção v1.2.0 ao changelog
   - Apontar para o GitHub Release

### No QGIS Plugin Repository:
1. **Submeter plugin:**
   - Upload de `smart_geotiff_exporter_v1.2.0.zip`
   - Confirmar metadata.txt (versão 1.2.0)
   - Aguardar aprovação (geralmente 24-48h)

---

## 📊 Resumo de Mudanças

| Categoria | Qtd | Detalhes |
|-----------|-----|----------|
| **Features Novas** | 1 | Valor NoData configurável na UI |
| **Melhorias** | 3 | Menu reorganizado, refatoração, docs |
| **Bugs Corrigidos** | 0 | Nenhum (v1.1.0 foi estável) |
| **Commits** | 5 | Desde v1.1.0 |

---

## ✨ Destaque Principal

> **NoData Configurável**
> Permite que usuários definam o valor NoData em vez de usar o hardcoded `0`, essencial para datasets onde 0 tem significado geográfico (contagem de pixels, índices espectrais, etc.).

---

## 🔗 Referências

- **Repository:** https://github.com/geoigarashi/smart_geotiff_exporter
- **Versão:** 1.2.0
- **QGIS Min:** 3.16
- **Autor:** Clayton Igarashi

---

**Status:** ✅ Pronto para lançamento público

Gerado em 26/03/2026
