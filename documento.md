# Projeto QGIS: mapas individuais de Contrato, RCP e sobreposição por RefBacen

## 1. Objetivo deste documento

Este documento registra o fluxo desenvolvido no QGIS para:

- reunir arquivos KML de glebas de **Contrato** e **RCP** em um GeoPackage;
- identificar corretamente cada par de arquivos;
- gerar mapas individuais por `id_par` usando o Atlas do Layout de Impressão;
- exibir apenas o Contrato, o RCP e a sobreposição pertencentes à página atual;
- mostrar tabelas com área das glebas, área de sobreposição e percentual;
- registrar o problema identificado no cálculo da sobreposição, para revisão do plugin/script.

O documento foi preparado como material de continuidade para revisão do script por outro agente.

---

## 2. Estrutura original dos arquivos

A pasta principal contém **146 subpastas**, nomeadas com o número da RefBacen.

Dentro de cada subpasta existe normalmente um par de arquivos KML no padrão:

```text
<refbacen>-<sequencial> <tipo>.kml
```

Exemplo:

```text
Pasta: 20230573214

20230573214-1 rcp.kml
20230573214-1 contrato.kml
```

### Exceção conhecida

A pasta `20191595422` possui dois pares:

```text
20191595422-1 contrato.kml
20191595422-1 rcp.kml
20191595422-2 contrato.kml
20191595422-2 rcp.kml
```

Portanto, embora existam 146 RefBacen, o controle do Atlas foi definido por `id_par`, pois o sequencial também precisa ser respeitado. Nesse modelo, a exceção gera duas páginas diferentes:

```text
20191595422-1
20191595422-2
```

---

## 3. Camada principal no GeoPackage

Um plugin próprio foi usado para mesclar os arquivos KML em uma camada do GeoPackage. A camada principal foi chamada, nos exemplos, de `proagro`.

Campos observados na tabela:

- `fid`
- `Arquivo`
- `Area_ha`
- `id_par`
- `origem`

Exemplo de registros:

```text
Arquivo                         id_par          origem
20190729697-1 contrato.kml      20190729697-1   contrato
20190729697-1 rcp.kml           20190729697-1   rcp
```

---

## 4. Criação do campo `id_par`

O campo `id_par` foi preenchido a partir do nome do arquivo, mantendo:

```text
<refbacen>-<sequencial>
```

Expressão utilizada:

```qgis
left("Arquivo", strpos("Arquivo", ' '))
```

Exemplo:

```text
20230573214-1 contrato.kml -> 20230573214-1
20230573214-1 rcp.kml      -> 20230573214-1
```

Observação: dependendo do comportamento esperado quanto ao espaço, uma alternativa mais explícita seria subtrair 1 da posição. Entretanto, a expressão acima foi a utilizada no projeto e o campo resultante funcionou no fluxo descrito.

---

## 5. Criação do campo `origem`

Foi criado o campo de texto `origem` para distinguir os dois tipos de arquivo.

Expressão efetivamente utilizada e registrada:

```qgis
regexp_substr(
    lower("Arquivo"),
    'rcp|contrato'
)
```

Resultados esperados:

```text
20230573214-1 rcp.kml      -> rcp
20230573214-1 contrato.kml -> contrato
```

---

## 6. Decisão sobre a unidade de produção dos mapas

Inicialmente foi considerada a possibilidade de gerar um mapa por RefBacen. No decorrer da configuração, ficou claro que o identificador mais seguro é o `id_par`, porque:

- o título desejado inclui o sequencial, por exemplo `20230165343-1`;
- Contrato e RCP devem ser pareados pelo mesmo RefBacen e sequencial;
- a RefBacen excepcional `20191595422` tem os sequenciais 1 e 2.

Assim, o Atlas deve gerar **uma página por `id_par`**.

---

## 7. Camada de cobertura do Atlas

Foi criada uma camada de cobertura dissolvendo a camada principal pelo campo:

```text
id_par
```

Nome sugerido para a camada:

```text
cobertura_id_par
```

Essa camada deve possuir uma única feição por `id_par` e serve para:

- controlar a página corrente do Atlas;
- fornecer a extensão da página;
- fornecer o valor de `id_par` aos filtros e textos dinâmicos.

No Layout de Impressão, a configuração do Atlas ficou conceitualmente assim:

```text
Gerar Atlas: ativado
Camada de cobertura: cobertura_id_par
Nome da página: id_par
Ordenação: id_par
```

O item de mapa foi configurado como **Controlado pelo Atlas**, com margem percentual ao redor da feição.

A camada de cobertura pode ficar sem símbolo, pois sua função é controlar o Atlas, não compor visualmente o mapa.

---

## 8. Título dinâmico

O título do mapa foi vinculado ao `id_par` da feição atual do Atlas.

Expressão:

```qgis
'Ref Bacen: ' || attribute(@atlas_feature, 'id_par')
```

Alternativa em texto dinâmico do Layout:

```qgis
Ref Bacen: [% attribute(@atlas_feature, 'id_par') %]
```

Exemplo exibido:

```text
Ref Bacen: 20230165343-1
```

---

## 9. Simbologia da camada principal baseada em regras

A camada principal `proagro` foi configurada com simbologia **Baseada em regras**.

### 9.1 Regra para Contrato

```qgis
lower(trim("origem")) = 'contrato'
AND
trim("id_par") = trim(attribute(@atlas_feature, 'id_par'))
```

Rótulo sugerido:

```text
Contrato
```

Estilo usado no mapa:

- preenchimento vermelho ou rosa semitransparente;
- contorno vermelho escuro.

### 9.2 Regra para RCP

```qgis
lower(trim("origem")) = 'rcp'
AND
trim("id_par") = trim(attribute(@atlas_feature, 'id_par'))
```

Rótulo sugerido:

```text
RCP
```

Estilo usado no mapa:

- preenchimento transparente;
- contorno azul tracejado.

### Resultado esperado

Em uma página como `20230165343-1`, somente devem ser desenhadas as duas feições cujo `id_par` seja exatamente:

```text
20230165343-1
```

Outros processos espacialmente próximos podem continuar existindo na camada, mas não devem ser renderizados nessa página.

---

## 10. Camada de interseção/sobreposição

Foi incluída uma camada produzida pelo plugin de cálculo de interseção. O nome visualizado foi semelhante a:

```text
Interseções (GeoInterseQ)
```

Campos observados:

- `type`
- `layer`
- `class`
- `area_m2`
- `area_ha`
- `percent`

O campo `class` contém valores equivalentes ao `id_par`, por exemplo:

```text
20190729697-1
20191008053-1
20191082526-2
```

### Regra usada para exibir somente a sobreposição da página atual

```qgis
trim("class") = trim(attribute(@atlas_feature, 'id_par'))
```

Rótulo sugerido:

```text
Sobreposição Contrato × RCP
```

Estilo usado no mapa:

- hachura ou pontilhado verde;
- preenchimento transparente ou semitransparente;
- contorno verde.

Essa regra apenas filtra a exibição conforme o valor gravado em `class`. A regra não corrige uma geometria de interseção calculada incorretamente pelo plugin.

---

## 11. Tabela de atributos das glebas no Layout

Foi adicionada uma tabela lateral/inferior com informações da camada principal, incluindo:

- Tipo;
- Área da gleba;
- Ref Bacen, representada pelo `id_par`.

### 11.1 Filtro correto da tabela pelo Atlas

A tabela inicialmente mostrava também feições de outros processos situados na mesma extensão do mapa. O problema foi corrigido aplicando um filtro próprio à tabela:

```qgis
trim("id_par") = trim(attribute(@atlas_feature, 'id_par'))
```

A opção de mostrar apenas feições visíveis no mapa não era suficiente, porque outras glebas espacialmente próximas também estavam dentro da extensão da página.

A configuração recomendada para a tabela é:

```text
Fonte: Feições da camada
Camada: proagro
Mostrar somente feições visíveis no mapa: desmarcado
Filtrar feições: marcado
```

Expressão do filtro:

```qgis
trim("id_par") = trim(attribute(@atlas_feature, 'id_par'))
```

### 11.2 Formatação do texto da coluna Tipo

Para exibir `contrato` como `Contrato` e `rcp` como `RCP`, foi usada uma expressão na coluna da tabela:

```qgis
CASE
    WHEN lower(trim("origem")) = 'contrato' THEN 'Contrato'
    WHEN lower(trim("origem")) = 'rcp' THEN 'RCP'
    ELSE "origem"
END
```

### 11.3 Formatação da área da gleba

Para limitar a quantidade de casas decimais apenas na apresentação do Layout:

```qgis
format_number("Area_ha", 4) || ' ha'
```

O número de casas pode ser ajustado conforme necessário. Nos mapas apresentados, a área das glebas foi exibida com quatro casas decimais.

---

## 12. Tabela de área e percentual da sobreposição

Foi incluída uma segunda tabela no Layout para mostrar:

- área da sobreposição;
- percentual de sobreposição.

### 12.1 Filtro da tabela de sobreposição

A tabela da camada de interseção deve ser filtrada usando o campo `class`:

```qgis
trim("class") = trim(attribute(@atlas_feature, 'id_par'))
```

### 12.2 Formatação da área de sobreposição

Exemplo com quatro casas decimais:

```qgis
format_number("area_ha", 4) || ' ha'
```

### 12.3 Formatação do percentual

Exemplo com duas casas decimais:

```qgis
format_number("percent", 2) || ' %'
```

Títulos adotados ou sugeridos:

```text
Área da sobreposição
Sobreposição (%)
```

---

## 13. Estado visual do Layout

O Layout contém:

- logomarca no cabeçalho;
- título dinâmico `Ref Bacen: <id_par>`;
- seta do norte;
- mapa principal;
- barra de escala;
- legenda;
- tabela das áreas de Contrato e RCP;
- tabela com área e percentual da sobreposição.

Legenda observada:

```text
Contrato
RCP
Sobreposição Contrato × RCP
```

---

## 14. Problema identificado no plugin de sobreposição

### 14.1 Caso observado

Na página do Atlas correspondente a:

```text
20230165343-1
```

as áreas exibidas na tabela das glebas foram:

```text
Contrato: 12,1699 ha
RCP:      12,9529 ha
```

Entretanto, a camada/tabela de sobreposição mostrou:

```text
Área da sobreposição: 37,8307 ha
Sobreposição:         95,58 %
```

A área de sobreposição exibida é maior que a área individual de cada uma das duas glebas do par corrente. Isso evidencia que a geometria ou a agregação gravada para esse `class` não representa apenas a interseção entre o Contrato e o RCP de `20230165343-1`.

### 14.2 Evidência espacial

Na mesma região existem glebas de outros processos. No painel de identificação foram visualizados quatro arquivos próximos/sobrepostos:

```text
20211032795-1 contrato.kml
20211032795-1 rcp.kml
20230165343-1 contrato.kml
20230165343-1 rcp.kml
```

O plugin aparentemente considerou sobreposições espaciais entre feições que pertencem a `id_par` diferentes e depois associou ou agregou o resultado de forma inadequada.

### 14.3 Distinção importante

Os filtros do Atlas e das tabelas agora estão funcionando corretamente. O Layout passa a exibir apenas registros cujo identificador coincide com a página atual.

Porém, o filtro do Layout não consegue corrigir uma feição de interseção que já foi calculada incorretamente. Se a geometria registrada com `class = '20230165343-1'` contém pedaços provenientes da interseção com `20211032795-1`, a regra de estilo continuará exibindo esses pedaços porque todos já fazem parte da mesma feição ou classe de saída.

---

## 15. Regra de negócio que o plugin deve respeitar

A interseção válida deve ser calculada **somente entre feições do mesmo `id_par`** e com origens opostas:

```text
Contrato(id_par = X) ∩ RCP(id_par = X)
```

Não devem ser calculadas ou agregadas como resultado do par X as combinações:

```text
Contrato(id_par = X) ∩ RCP(id_par = Y)
Contrato(id_par = Y) ∩ RCP(id_par = X)
Contrato(id_par = X) ∩ Contrato(id_par = Y)
RCP(id_par = X) ∩ RCP(id_par = Y)
```

quando `X <> Y`.

### Chave correta de pareamento

A chave principal deve ser:

```text
id_par = <refbacen>-<sequencial>
```

Não é suficiente usar somente proximidade espacial, interseção espacial, nome da camada genérica ou apenas RefBacen sem sequencial.

---

## 16. Estratégia recomendada para revisão do script

A revisão deve localizar no código:

1. onde as feições de Contrato são selecionadas;
2. onde as feições de RCP são selecionadas;
3. onde os pares candidatos são formados;
4. onde a operação geométrica de interseção é executada;
5. onde múltiplos resultados são dissolvidos ou agregados;
6. onde o campo `class` é atribuído;
7. como `area_m2`, `area_ha` e `percent` são calculados.

### Fluxo lógico desejado

```text
Para cada id_par único:
    selecionar apenas as feições com esse id_par
    separar origem = contrato
    separar origem = rcp
    corrigir geometrias inválidas, se necessário
    unir as partes do contrato do mesmo id_par, se houver múltiplas
    unir as partes do rcp do mesmo id_par, se houver múltiplas
    calcular interseção(contrato_atual, rcp_atual)
    gravar class = id_par atual
    calcular area_m2 da interseção
    calcular area_ha = area_m2 / 10000
    calcular percent conforme denominador definido
```

### Pseudocódigo de referência

```python
for id_par in ids_unicos:
    contratos = feicoes[(feicoes["id_par"] == id_par) &
                         (feicoes["origem"] == "contrato")]

    rcps = feicoes[(feicoes["id_par"] == id_par) &
                   (feicoes["origem"] == "rcp")]

    if not contratos or not rcps:
        registrar_pendencia(id_par, "Par incompleto")
        continue

    geom_contrato = unir_geometrias(contratos)
    geom_rcp = unir_geometrias(rcps)

    sobreposicao = intersecao(geom_contrato, geom_rcp)

    if sobreposicao_vazia(sobreposicao):
        registrar_resultado_sem_intersecao(id_par)
        continue

    area_intersecao = calcular_area(sobreposicao)

    gravar_resultado(
        geometry=sobreposicao,
        class=id_par,
        area_m2=area_intersecao,
        area_ha=area_intersecao / 10000,
        percent=calcular_percentual(...)
    )
```

Esse pseudocódigo registra a regra de negócio, não uma implementação pronta para uma API específica do QGIS.

---

## 17. Definição do percentual precisa ser confirmada

O script deve deixar explícito qual é o denominador do percentual. Possibilidades comuns:

### Percentual da área do RCP coberta pelo Contrato

```text
percentual = área_interseção / área_RCP × 100
```

### Percentual da área do Contrato coberta pelo RCP

```text
percentual = área_interseção / área_Contrato × 100
```

### Percentual em relação à menor gleba

```text
percentual = área_interseção / min(área_RCP, área_Contrato) × 100
```

A opção correta deve ser definida conforme a regra do negócio. Sem essa definição, o campo `percent` pode ser matematicamente calculado, mas semanticamente ambíguo.

---

## 18. Validações automáticas recomendadas

### 18.1 Limite geométrico obrigatório

Para cada `id_par`:

```text
área_interseção <= área_contrato
área_interseção <= área_rcp
```

Equivalentemente:

```text
área_interseção <= min(área_contrato, área_rcp)
```

Se isso falhar, o resultado deve ser marcado como erro e não deve ser aceito silenciosamente.

### 18.2 Validação da chave

Todo resultado deve conter um único `class` correspondente ao `id_par` usado nos dois lados do cálculo.

### 18.3 Validação de pares incompletos

O script deve identificar casos em que existe somente:

- Contrato sem RCP; ou
- RCP sem Contrato.

### 18.4 Validação de duplicidade

O script deve tratar explicitamente múltiplas feições com mesmo `id_par` e mesma `origem`. Antes da interseção, pode ser necessário unir as partes da mesma origem dentro do mesmo par.

### 18.5 Validação de geometria

Antes do cálculo, verificar se as geometrias são válidas. Caso não sejam, registrar a ocorrência e aplicar uma correção geométrica controlada, conforme a implementação escolhida.

### 18.6 Validação do sistema de referência

Os cálculos de área devem ocorrer em um sistema de referência adequado para medição de área. O script deve registrar o CRS usado no cálculo.

### 18.7 Relatório de controle

Gerar um relatório com, no mínimo:

```text
id_par
quantidade_contrato
quantidade_rcp
area_contrato_ha
area_rcp_ha
area_intersecao_ha
percentual
erro_validacao
```

---

## 19. Caso de teste prioritário

Usar como teste de regressão:

```text
id_par: 20230165343-1
```

Entradas do par:

```text
20230165343-1 contrato.kml
20230165343-1 rcp.kml
```

Glebas vizinhas que não podem participar do cálculo:

```text
20211032795-1 contrato.kml
20211032795-1 rcp.kml
```

Valores observados nas entradas do par:

```text
Área Contrato: 12,1699 ha
Área RCP:      12,9529 ha
```

Condição mínima para o resultado corrigido:

```text
Área da interseção <= 12,1699 ha
```

O valor anteriormente produzido, `37,8307 ha`, deve ser tratado como evidência de cálculo ou agregação incorreta para esse `id_par`.

---

## 20. Checklist para o próximo agente

- [ ] Examinar o código completo do plugin.
- [ ] Identificar a função que forma os pares de feições.
- [ ] Confirmar se o pareamento usa `id_par` antes da interseção espacial.
- [ ] Verificar se existem loops que cruzam todas as feições contra todas as demais.
- [ ] Verificar o uso de índice espacial e os filtros de atributos aplicados após a busca de candidatos.
- [ ] Confirmar se o resultado de um processo está sendo dissolvido com o de outro.
- [ ] Verificar em qual etapa o campo `class` recebe o identificador.
- [ ] Confirmar o denominador usado no campo `percent`.
- [ ] Adicionar a validação `área_interseção <= min(área_contrato, área_rcp)`.
- [ ] Testar `20230165343-1` isoladamente.
- [ ] Testar `20230165343-1` com todas as glebas vizinhas carregadas.
- [ ] Testar a exceção `20191595422-1` e `20191595422-2`.
- [ ] Comparar os resultados isolados com os resultados em lote.
- [ ] Regerar a camada de interseção.
- [ ] Atualizar as tabelas e o Atlas no Layout.

---

## 21. Expressões consolidadas

### Campo `id_par`

```qgis
left("Arquivo", strpos("Arquivo", ' '))
```

### Campo `origem`

```qgis
regexp_substr(
    lower("Arquivo"),
    'rcp|contrato'
)
```

### Regra Contrato

```qgis
lower(trim("origem")) = 'contrato'
AND
trim("id_par") = trim(attribute(@atlas_feature, 'id_par'))
```

### Regra RCP

```qgis
lower(trim("origem")) = 'rcp'
AND
trim("id_par") = trim(attribute(@atlas_feature, 'id_par'))
```

### Regra da camada de sobreposição

```qgis
trim("class") = trim(attribute(@atlas_feature, 'id_par'))
```

### Filtro da tabela de Contrato e RCP

```qgis
trim("id_par") = trim(attribute(@atlas_feature, 'id_par'))
```

### Filtro da tabela de sobreposição

```qgis
trim("class") = trim(attribute(@atlas_feature, 'id_par'))
```

### Título dinâmico

```qgis
'Ref Bacen: ' || attribute(@atlas_feature, 'id_par')
```

### Formatação do Tipo

```qgis
CASE
    WHEN lower(trim("origem")) = 'contrato' THEN 'Contrato'
    WHEN lower(trim("origem")) = 'rcp' THEN 'RCP'
    ELSE "origem"
END
```

### Área da gleba

```qgis
format_number("Area_ha", 4) || ' ha'
```

### Área de sobreposição

```qgis
format_number("area_ha", 4) || ' ha'
```

### Percentual de sobreposição

```qgis
format_number("percent", 2) || ' %'
```

---

## 22. Conclusão

A configuração do Atlas, da simbologia e das tabelas foi estruturada para filtrar corretamente cada página por `id_par`. O problema remanescente não está no Layout: está na camada de interseção gerada pelo plugin.

A revisão do plugin deve garantir que a sobreposição seja calculada exclusivamente entre Contrato e RCP do mesmo `id_par`, antes de qualquer agregação. O caso `20230165343-1` deve ser usado como teste principal, pois evidencia a contaminação do resultado por glebas espacialmente próximas pertencentes a outro processo.
