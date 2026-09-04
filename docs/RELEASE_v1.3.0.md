# 🌐 GeoInterseQ — v1.3.0

**Data de Lançamento:** 04 de setembro de 2026

---

## ✨ Destaques da Versão

### 🚀 Assistente de Autoinstalação de Dependências com 1 Clique
* **Instalação Sem Complicações:** Usuários leigos não precisam mais abrir o OSGeo4W Shell, terminal ou executar comandos manuais para instalar bibliotecas como `rasterio` e `shapely`.
* **Zero Privilégios de Administrador (`--user`):** A rotina de instalação do `pip` direciona os pacotes diretamente para o diretório de usuário (`site.getusersitepackages()`), evitando erros de permissão de escrita em pastas do sistema como `C:\Program Files\QGIS`.
* **Eliminação de Pop-ups Invasivos no Boot do QGIS:** O alerta bloqueante (`QMessageBox.warning`) que era disparado em computadores recém-configurados na inicialização do QGIS foi completamente removido do `__init__.py`, registrando apenas uma notificação informativa silenciosa no `QgsMessageLog`.
* **Interface Fluente com Worker Assíncrono (`QThread`):** A instalação executa em segundo plano sem congelar a interface gráfica do QGIS, apresentando barra de progresso visual e terminal de log recolhível com detalhes em tempo real.
* **Tentativa de Carregamento a Quente (*Hot-Reload*):** Injeta dinamicamente a pasta de pacotes do usuário no `sys.path`, invalida caches de importação e tenta carregar as bibliotecas na mesma sessão, solicitando reinício do software apenas se houver vinculação travada de DLLs nativas no Windows.

---

## 📋 Resumo de Mudanças

### 🌟 Novas Funcionalidades (v1.3.0)
- 🧩 **Módulo Dedicado `dependency_installer.py`:** Arquitetura limpa e modular com `DependencyInstallWorker` (QThread), `DependencyManager` e `DependencyInstallerDialog` (PyQt5 fluente sem arquivos `.ui`).
- 🎯 **Gatilho Guiado e Inteligente:** O assistente é acionado de forma convidativa ao abrir o GeoInterseQ ou ao tentar adicionar uma camada raster pela primeira vez.
- 🛡️ **Tratamento Defensivo:** Se o usuário optar por não instalar dependências ou não tiver conexão com a internet, a análise puramente vetorial continua funcionando com 100% de estabilidade.

### 🧹 Refatorações e Melhorias de Arquitetura
- 🛠️ **Inicialização Silenciosa:** `__init__.py` desacoplado de caixas de diálogo modais durante a carga do QGIS.
- 🛠️ **Eliminação do DeprecationWarning de Filtros (`setFilters`):** Migração de `QgsMapLayerProxyModel` para `Qgis.LayerFilter` (API moderna introduzida no QGIS 3.34+) com fallback transparente para versões legadas, eliminando advertências no Registro de Mensagens do QGIS.
- 🛠️ **Eliminação do DeprecationWarning de Atributos (`QgsField`):** Atualização dos construtores de `QgsField` na geração de camadas de saída temporárias para a API moderna `QMetaType` (QGIS 3.38+), substituindo `QVariant.Type` com compatibilidade retroativa total.
- 🛠️ **Tratamento Seguro de Exceções:** Inclusão de blocos `try...except ImportError` defensivos ao acessar métodos que exigem o `rasterio`.
- 🛠️ **Conformidade PEP8 & Ruff:** Tipagem estrita Python 3.12+, uso exclusivo de `pathlib.Path` e docstrings detalhadas no formato Google.
- 🛠️ **Eliminação do ResourceWarning no Pip Worker:** Gerenciamento determinístico de streams via context manager no pipe `stdout` do subprocesso assíncrono, evitando advertências de arquivos não fechados durante a coleta de lixo.



---

## 🎨 Compatibilidade

- **QGIS:** 3.16+ (testado e homologado nas versões QGIS LTR e QGIS 3.44+)
- **Python:** 3.12+ (Type hints modernos, PEP8 e compatível com Ruff)
- **Dependências Gerenciadas:** `rasterio`, `shapely`

---

## 📦 Conteúdo do Pacote

```
geointerseq_v1.3.0.zip
└── GeoInterseQ/
    ├── __init__.py                # Inicialização e registro silencioso de logs
    ├── dependency_installer.py    # Assistente gráfico e worker assíncrono pip
    ├── metadata.txt               # Versão 1.3.0 e changelog
    ├── icon.png                   # Ícone oficial do plugin
    ├── Logo-GEO-HQ.svg            # Logotipo vetorizado Plataforma Geo
    ├── README.md                  # Guia atualizado com assistente 1 clique
    └── geo_interseq.py            # Interface principal e motor analítico geoespacial
```

---

## 🚀 Como Atualizar

1. Obtenha o pacote `geointerseq_v1.3.0.zip` no diretório `plugins_zip/`.
2. No menu superior do QGIS, acesse **Plugins > Gerenciar e Instalar Plugins > Instalar a partir de arquivo ZIP**.
3. Selecione o arquivo e clique em **Instalar Plugin**.
