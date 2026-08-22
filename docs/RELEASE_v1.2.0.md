# 🌐 GeoInterseQ — v1.2.0

**Data de Lançamento:** 30 de maio de 2026

---

## ✨ Destaques da Versão

### 📐 Recorte Vetorial Exato (Clip) e Precisão Geodésica
* **Recorte de Borda (Clip):** As geometrias geradas a partir de dados raster são agora geometricamente recortadas (clipped) pela Shapely com a geometria exata do imóvel (camada base). Isso elimina as bordas serrilhadas características dos pixels que extrapolavam o limite do imóvel, garantindo consistência visual e espacial.
* **Cálculo de Área Geodésica:** Substituição do cálculo planar no CRS UTM local pela API `QgsDistanceArea` do QGIS na elipsoide do projeto. Isso garante **100% de paridade** com a calculadora de campo do QGIS (expressão `$area`), eliminando discrepâncias sistemáticas de distorção de escala em projeções planares.

### 🎨 Nova Interface e Experiência do Usuário (UI/UX)
* **Painel de Dicas & Tutorial:** Inclusão de uma nova seção lateral à direita contendo o logotipo da **Plataforma Geo e Inovação** e o ícone da ferramenta **GeoInterseQ** dispostos lado a lado, acompanhados de um mini guia rápido com boas práticas e dicas de uso.
* **Dimensionamento Inteligente:** Ajuste vertical automático para exibição integral do conteúdo. Implementação de proteção contra telas de baixa resolução: os logotipos e a janela se ajustam dinamicamente para que a interface do plugin nunca ultrapasse a altura total disponível na tela do usuário.
* **Documentação com Identidade Visual:** O [README.md](file:///c:/Python/QGIS%20Plugins/GeoInterseQ/README.md) agora exibe de forma integrada no topo o ícone da ferramenta e o logotipo corporativo lado a lado.

### 🗂️ Organização no Projeto e Tabela de Atributos
* **Grupo de Resultados:** Criação automática do grupo `"Resultados GeoInterseQ"` na raiz da árvore de camadas do QGIS. Todas as camadas de interseção geradas pelo plugin são inseridas de forma organizada dentro deste grupo.
* **Coluna `area_ha`:** Adição da coluna `area_ha` (área calculada em hectares) na tabela de atributos das camadas temporárias resultantes, complementando o campo original de metros quadrados.

---

## 📋 Resumo de Mudanças

### ✅ Novas Funcionalidades (v1.2.0)
- 🖥️ Painel lateral direito de ajuda com tutorial rápido integrado.
- 🖼️ Exibição lado a lado dos logotipos corporativo e da ferramenta na interface do plugin e no `README.md`.
- 📐 Recorte vetorial exato (`intersection`) das feições raster pela base.
- 🌍 Cálculo de áreas baseado em elipsoide (idêntico à calculadora `$area`).
- 📁 Criação e agrupamento automático em `"Resultados GeoInterseQ"` no painel de camadas.
- 📊 Nova coluna `area_ha` gravada na tabela de atributos das camadas de interseção.

### 🔧 Ajustes de Responsividade e Ergonomia
- 📏 Altura inicial adaptada ao conteúdo do tutorial.
- 🔍 Redimensionamento automático do layout e das imagens com base no tamanho útil da tela do usuário.

---

## 🎨 Compatibilidade

- **QGIS:** 3.16+
- **Python:** 3.12+ (Tipo de sintaxe moderno e Ruff-compatible)
- **Dependências:** Rasterio, Shapely, Pyproj, NumPy

---

## 📦 Conteúdo do Pacote

```
geointerseq_v1.2.0.zip
└── GeoInterseQ/
    ├── __init__.py          # Inicialização e validação de dependências
    ├── metadata.txt         # Versão e histórico detalhado (changelog)
    ├── icon.png             # Ícone do plugin
    ├── Logo-GEO-HQ.svg      # Logotipo vetorizado Plataforma Geo
    ├── README.md            # Guia de instalação e pré-requisitos
    └── geo_interseq.py      # Lógica de interface PyQt5 e backend geoespacial
```

---

## 🚀 Como Instalar

### Opção 1: Via Gerenciador de Plugins do QGIS (ZIP)
1. No menu superior do QGIS, vá em **Plugins → Gerenciar e Instalar Plugins...**
2. Vá na aba **Instalar a partir de arquivo ZIP**.
3. Selecione o arquivo `geointerseq_v1.2.0.zip` gerado.
4. Clique em **Instalar plugin**.

### Opção 2: Instalação Manual
1. Extraia o arquivo `geointerseq_v1.2.0.zip` dentro da pasta de plugins do perfil do QGIS:
   * **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   * **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
2. Reinicie o QGIS.
3. Ative o plugin em **Plugins → Gerenciar e Instalar Plugins... → Instalados** marcando a caixa correspondente ao **GeoInterseQ**.

---

## 🐛 Correções de Bugs
- ✅ Corrigido o extrapolo da borda serrilhada do raster sobre o polígono limitante.
- ✅ Resolvida a discrepância de cálculo de áreas entre o algoritmo e a calculadora de campo do QGIS.
- ✅ Removida duplicidade visual na marca corporativa do cabeçalho.

---

## 📞 Suporte e Repositório

- **Repositório:** [GitHub - geo-interseq](https://github.com/geoigarashi/geo-interseq)
- **Autor/Mantenedor:** Plat. Geo e Inovação
- **Erros e Sugestões:** Abrir uma Issue no repositório GitHub.

---

**Plataforma Geo e Inovação — Tecnologia a serviço da inteligência territorial. 🌾**
