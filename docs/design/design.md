# Coxinh.IA

Especificação de identidade visual e interface

Versão: 0.1.0  
Data: 14/11/2026  
Frontend: Streamlit  
Idioma: português do Brasil

## 1. Objetivo

Orientar a implementação do frontend do Coxinh.IA com uma identidade consistente, baseada nas referências visuais fornecidas e compatível com o Streamlit. Este documento define aparência, composição, componentes e apresentação dos estados do produto.

O Coxinh.IA é uma experiência de chat para criar invenções de coxinha a partir dos ingredientes, utensílios e meios de preparo informados pelo usuário. A interface acompanha Chef, Subchef, Impasse, Cozinheiro e Consumo, mantendo a conversa como elemento principal.

As regras de aprovação, o limite de rejeições e os critérios de consumo pertencem à especificação funcional. A interface apresenta as decisões recebidas do sistema; não cria decisões ou classificações próprias.

## 2. Direção visual

### 2.1 Referência principal

A imagem `image(20261114-231958).png` orienta a composição: fundo preto, tipografia branca de grande presença, muito espaço livre e um volume abstrato construído por linhas curvas em verde, ciano e azul.

O preto, o branco e o verde `#86BC25` têm respaldo na paleta publicada pela Deloitte [1]. Os demais tokens, dimensões e tratamentos deste documento são decisões de design para o Coxinh.IA. Este documento não reproduz um manual oficial completo da Deloitte.

### 2.2 Aplicação ao Coxinh.IA

1. Usar preto como fundo dominante da aplicação.
2. Usar branco para conteúdo principal e títulos.
3. Reservar o verde para a identidade da marca e a ação principal.
4. Usar ciano e azul nas curvas decorativas e em detalhes de interação definidos neste documento.
5. Manter a composição limpa, com poucas superfícies e hierarquia evidente.
6. Usar exclusivamente a marca Coxinh.IA na aplicação. A palavra Deloitte e os textos institucionais da referência não compõem a interface.
7. Dar à invenção um tom criativo; manter controles, mensagens de erro e pareceres objetivos.

### 2.3 Tratamentos a evitar

* Fundo geral cinza ou aparência de painel administrativo padrão.
* Gradientes ocupando grandes fundos, vidro translúcido e brilho neon espalhado.
* Emojis decorativos, robôs, mascotes ou ícones de cozinha adicionados à identidade.
* Slogans, frases motivacionais, estatísticas demonstrativas e cartões sem função.
* Sombras intensas, bordas muito arredondadas e botões em formato de cápsula.
* Fotografias de coxinhas genéricas substituindo o elemento abstrato na abertura.
* A imagem de referência inteira aplicada como fundo: ela serve para orientar a composição, não como peça pronta da interface.

## 3. Marca e arquivos de referência

A grafia é sempre **Coxinh.IA**. Preservar a coxinha vazada branca, o ponto verde do símbolo e o ponto verde presente no nome, conforme os arquivos fornecidos.

| Arquivo fornecido | Papel no projeto |
| --- | --- |
| `Coxinh.IA marca.png` | Referência do símbolo isolado, branco com ponto verde. |
| `Coxinh.IA  logo nome.png` | Referência da escrita da marca. O nome do arquivo original contém dois espaços antes de `logo`. |
| `Coxinh.IA site.png` | Referência anterior de aplicação da marca e de apresentação de imagens de coxinha. |
| `Coxinh.IA fachada.png` | Referência da combinação entre símbolo e nome. |
| `image(20261114-231958).png` | Referência principal de composição, contraste e curvas abstratas. |

A referência mais recente orienta o fundo preto e o grafismo. O mockup anterior do site não obriga a implementação de uma galeria, uma seção branca ou um formulário separado do chat.

### 3.1 Uso da marca

* No cabeçalho, combinar símbolo e nome, alinhados à esquerda.
* Altura visual do símbolo: 40 px no desktop e 32 px no celular.
* Largura visual sugerida do nome: entre 170 e 220 px no desktop, ajustada proporcionalmente no celular.
* Manter pelo menos metade da altura do símbolo como espaço livre ao redor da composição.
* Preservar a proporção; nunca esticar, inclinar ou aplicar sombra ao logo.
* Não substituir o símbolo por emoji ou ícone genérico de gota.
* Para uma área compacta, usar somente o símbolo com nome acessível `Coxinh.IA`.

Os PNGs fornecidos têm áreas de respiro próprias. Preparar versões de exibição com limites adequados antes da implementação definitiva, preservando o desenho. SVG, versões transparentes e favicon são ativos a preparar; não são entregáveis existentes deste documento.

## 4. Paleta e tokens

Um token é um nome estável para uma decisão visual. A implementação deve reutilizar esses nomes para evitar cores diferentes entre telas e componentes.

| Token | Valor | Aplicação |
| --- | --- | --- |
| `background` | `#000000` | Fundo principal e cabeçalho. |
| `surface` | `#0C0C0C` | Blocos discretos dentro da conversa. |
| `surface-raised` | `#151515` | Entrada de texto, mensagens do usuário e áreas interativas. |
| `text-primary` | `#FFFFFF` | Títulos e conteúdo principal. |
| `text-secondary` | `#B7BCC5` | Informações auxiliares, sem reduzir sua legibilidade. |
| `brand-green` | `#86BC25` | Destaque da marca e ação principal. |
| `brand-green-hover` | `#98CE38` | Passagem do ponteiro sobre a ação principal. |
| `on-brand` | `#000000` | Texto sobre o verde da ação principal. |
| `border-subtle` | `#333333` | Divisórias decorativas e separações de superfície. |
| `border-control` | `#757575` | Limites de campos e controles quando necessários para identificá-los. |
| `focus` | `#5BD9D0` | Contorno visível de foco pelo teclado. |
| `art-cyan` | `#5BD9D0` | Linhas claras do grafismo. |
| `art-blue` | `#4DA8D8` | Linhas intermediárias do grafismo. |
| `art-deep-blue` | `#3864A4` | Linhas de profundidade do grafismo; não usar para texto pequeno. |
| `warning` | `#F3C969` | Destaque de atenção e decisão pendente. |
| `danger` | `#FF8A80` | Destaque de reprovação para consumo e falhas relevantes. |

### 4.1 Regras de contraste

* Texto normal deve atingir contraste mínimo de 4,5:1; texto grande, 3:1, conforme WCAG [9].
* Botões verdes usam texto preto. Branco sobre `#86BC25` tem contraste aproximado de 2,27:1 e não é a combinação definida para esses botões.
* Preto sobre `#86BC25` tem contraste aproximado de 9,23:1.
* `text-secondary` sobre preto tem contraste aproximado de 11,01:1.
* `border-control` sobre `surface-raised` tem contraste aproximado de 3,96:1.
* As proporções acima foram calculadas para cores opacas. Transparência e mistura com imagens exigem nova verificação.
* Não depender de verde e vermelho para distinguir estados. Sempre apresentar um rótulo textual.

## 5. Tipografia

Usar uma família sem serifa, com títulos fortes e texto simples. A escolha inicial para a interface é **Arial**, com alternativas **Helvetica** e **sans-serif**, disponíveis conforme o ambiente do usuário. Essa é uma escolha do projeto, não uma afirmação sobre a fonte oficial da Deloitte.

O lettering do nome Coxinh.IA permanece no ativo fornecido; não tentar reconstruí-lo digitando o nome com a fonte da interface.

| Uso | Desktop | Celular | Peso |
| --- | --- | --- | --- |
| Título de abertura | 48 a 52 px | 32 a 36 px | 700 |
| Título do resultado | 28 a 32 px | 24 a 28 px | 700 |
| Título de seção | 22 a 24 px | 20 a 22 px | 700 |
| Texto da conversa e receita | 16 px | 16 px | 400 |
| Botões e rótulos | 16 px | 16 px | 600 ou 700 |
| Informação auxiliar | 14 px | 14 px | 400 |

Entrelinha do conteúdo: 1,5 a 1,6. Títulos: 1,1 a 1,2. Preferir unidades relativas na implementação para respeitar ampliação de texto.

Evitar parágrafos em letras maiúsculas. Reservar negrito para títulos, rótulos e trechos necessários à leitura.

## 6. Espaçamento e geometria

| Elemento | Diretriz |
| --- | --- |
| Escala de espaçamento | 4, 8, 12, 16, 24, 32, 48 e 64 px. |
| Conteúdo geral | Centralizado, largura máxima aproximada de 1120 px. |
| Leitura da conversa | Largura máxima aproximada de 760 px. |
| Margens laterais | 32 px em telas amplas; 16 px em telas pequenas. |
| Intervalo entre seções | 32 a 48 px. |
| Espaçamento interno de blocos | 20 a 24 px; 16 px no celular. |
| Raio de campos e cartões | 8 px. |
| Raio de botões | 6 px. |
| Bordas | 1 px; foco com contorno de 2 px e afastamento de 2 px. |
| Alvo de interação | Altura e área útil desejadas de pelo menos 44 px. |

Evitar colocar todo conteúdo dentro de cartões. A conversa deve respirar sobre o fundo preto; superfícies servem para separar mensagens do usuário, decisões e resultados.

## 7. Grafismo de linhas curvas

### 7.1 Aparência

Criar um elemento original inspirado na construção da referência: curvas finas, sobrepostas, com pontos de convergência e sensação de volume. A silhueta geral pode sugerir uma coxinha ou gota, mantendo o logo separado e reconhecível.

* Entre 18 e 28 curvas, com espessura aparente de 1 a 2 px no desktop.
* Alternância ou transição suave entre verde, ciano e azul, restrita aos traços.
* Fundo transparente sobre o preto da página.
* Sem preenchimento sólido, esfera 3D, sombra projetada ou textura ruidosa.
* Opacidade entre 65% e 90% na abertura; reduzir quando houver conteúdo próximo.
* Espaço próprio na composição; não cruzar letras, campos ou botões.

### 7.2 Posicionamento e comportamento

No desktop, posicionar à direita da abertura, em uma área aproximada de 360 a 480 px. O título e a orientação do chat ficam à esquerda.

Em telas menores, reduzir o grafismo para até 220 px ou ocultá-lo quando prejudicar a área do chat. A escolha deve ser feita por CSS responsivo sobre o elemento decorativo, sem depender de chamadas ao modelo.

Após o primeiro envio, recolher a abertura e retirar o grafismo grande. A conversa passa a ocupar o espaço principal.

A primeira implementação usa grafismo estático em SVG ou imagem local. Animação é opcional para uma etapa posterior e deve respeitar a preferência de movimento reduzido. O grafismo é decorativo e deve ser ignorado por leitores de tela.

## 8. Composição da interface

### 8.1 Cabeçalho

Cabeçalho compacto, preto, com a marca à esquerda e uma divisória discreta quando necessária. Evitar navegação extensa.

Uma ação `Nova criação` pode aparecer quando já houver conversa. Ela inicia uma nova execução; não deve apagar silenciosamente uma criação ainda em processamento ou aguardando decisão.

Não implementar telas de login, dashboards, menus de configuração de modelo ou estatísticas como parte desta especificação visual. `Minhas receitas`, presente no mockup anterior, depende de uma definição funcional de histórico antes de entrar na navegação.

### 8.2 Estado inicial

1. Marca no cabeçalho.
2. Título: `Crie sua coxinha`.
3. Orientação funcional: `Descreva os ingredientes, utensílios e meios de preparo que você tem.`
4. Grafismo de curvas à direita, quando houver espaço.
5. Entrada de chat imediatamente disponível, sem exigir navegação ou formulário preliminar.

Não preencher a abertura com exemplos automáticos, receitas de demonstração, slogans ou uma galeria fictícia.

### 8.3 Conversa

* Um único fluxo de mensagens representa a interação do usuário com o sistema.
* Mensagem do usuário em `surface-raised`, com texto branco e identificação textual.
* Resposta do sistema sobre preto ou `surface`, sem uma moldura por parágrafo.
* Identificar o interlocutor como `Você` e `Coxinh.IA`; os nomes dos nós aparecem no acompanhamento do processo.
* Evitar cinco conversas paralelas ou cinco colunas para representar os agentes.
* O campo aceita texto livre com ingredientes e recursos no mesmo pedido.
* Texto indicativo do campo: `Digite seus ingredientes, utensílios e meios de preparo`.
* Manter identificação acessível do campo mesmo quando o texto indicativo desaparecer.

### 8.4 Acompanhamento do processo

Apresentar um bloco compacto de status, próximo à última mensagem. A etapa atual fica visível; detalhes podem ser expandidos.

| Etapa recebida | Texto de interface |
| --- | --- |
| Chef | `Chef elaborando a receita` |
| Subchef | `Subchef revisando a proposta` |
| Nova tentativa | `Chef ajustando a proposta` |
| Impasse | `Aguardando sua decisão` |
| Cozinheiro | `Cozinheiro preparando o resultado` |
| Geração da imagem | `Gerando a imagem da coxinha` |
| Consumo | `Analisando a possibilidade de consumo` |
| Finalização | `Criação concluída` |

Esses textos só aparecem quando corresponderem ao estado real. Não usar temporizadores para simular trabalho, porcentagens inventadas ou mensagens de conclusão antecipadas.

Exibir tentativa atual e limite somente quando esses dados forem fornecidos pela execução. Não fixar o número de rejeições no frontend.

### 8.5 Impasse

Exibir a decisão dentro da conversa, em um bloco de largura completa. A informação precisa permanecer visível enquanto o sistema aguarda o usuário.

Conteúdo, nesta ordem:

1. Título: `Não foi possível aprovar a proposta`.
2. Motivos das rejeições em linguagem compreensível.
3. Proposta atual disponível para consulta.
4. Pergunta: `Deseja continuar a criação mesmo assim?`.
5. Ações: `Continuar criação` e `Encerrar`.

As duas ações devem ser legíveis, próximas e de peso visual equivalente, com estilo secundário neutro. Não usar verde de aprovação no botão de continuidade. Não destacar uma opção para induzir a decisão.

Durante o envio da escolha, bloquear cliques repetidos. Após a confirmação, mostrar a decisão registrada. `Continuar criação` não deve ser renomeado para `Aprovar consumo`.

### 8.6 Resultado

Organizar a resposta final em uma coluna, com leitura natural:

1. Nome da invenção, quando fornecido pelo sistema.
2. Parecer de consumo, em bloco visível antes do modo de preparo.
3. Imagem gerada, com descrição acessível.
4. Ingredientes da proposta final.
5. Modo de preparo em passos numerados, conforme o conteúdo autorizado para apresentação pelo backend.

O nó Consumo executa depois do Cozinheiro no fluxo definido. A ordem de leitura da resposta final pode destacar o parecer antes dos demais conteúdos, sem alterar a ordem de execução dos nós.

Preservar proporção da imagem, sem recortar a coxinha para preencher um cartão. Usar `Imagem gerada por IA` como identificação funcional da representação. O fundo da página continua preto; o fundo da própria imagem pode variar conforme a criação.

O parecer apresenta o estado e a justificativa recebidos. Uma criação concluída não recebe automaticamente um selo de segurança. Se o parecer estiver pendente ou indisponível, mostrar essa condição explicitamente.

### 8.7 Apresentação dos pareceres

Os nomes definitivos das classificações serão definidos pelas regras de consumo. A correspondência visual deve seguir estas funções:

| Condição informada pelo sistema | Tratamento visual |
| --- | --- |
| Consumo liberado conforme as regras | Rótulo explícito, justificativa e destaque discreto; sem garantia genérica de segurança absoluta. |
| Ressalva ou atenção | Rótulo textual e detalhe em `warning`. |
| Consumo reprovado | Rótulo textual, motivo visível e detalhe em `danger`. |
| Avaliação pendente ou inconclusiva | Rótulo textual neutro e motivo; não representar como aprovação. |

Não esconder a reprovação dentro de um expansor. Uma escolha de continuidade no Impasse deve permanecer distinguível da decisão do nó Consumo.

### 8.8 Erros e recuperação

Mostrar mensagens curtas, vinculadas à etapa afetada, preservando o conteúdo já obtido.

| Ocorrência | Apresentação esperada |
| --- | --- |
| Entrada vazia | Não iniciar processamento; manter o campo disponível. |
| Falha de serviço | Identificar a etapa que falhou e informar a possibilidade real de nova tentativa. |
| Falha de geração da imagem | Preservar o texto disponível e mostrar `Não foi possível gerar a imagem`. |
| Parecer indisponível | Mostrar `Avaliação de consumo indisponível`; não inferir liberação. |
| Decisão já registrada | Apresentar a decisão existente, sem reenviar a ação. |
| Execução já atualizada | Atualizar a visualização a partir do estado atual, sem manter uma decisão antiga como pendente. |
| Encerramento pelo usuário | Mostrar `Criação encerrada` e o motivo disponível. |

Só exibir uma ação de recuperação quando ela estiver implementada e for válida para o estado atual. Detalhes técnicos completos ficam fora da conversa principal.

## 9. Implementação visual em Streamlit

### 9.1 Estratégia

Usar primeiro o tema nativo e os componentes do Streamlit. Centralizar cores, tipografia e geometria em `.streamlit/config.toml`; o suporte oficial a temas permite configurar a aparência da aplicação [2][3].

Usar CSS próprio apenas para completar a composição, o grafismo, a responsividade e ajustes que não tenham opção nativa. O frontend continua sendo Streamlit; esta especificação não depende de React ou de um servidor de interface adicional.

### 9.2 Correspondência de tema

Esta tabela descreve os valores a configurar; não é um arquivo de implementação já criado.

| Chave em `[theme]` | Valor de referência | Função |
| --- | --- | --- |
| `base` | `dark` | Base escura. |
| `primaryColor` | `#86BC25` | Cor principal. |
| `backgroundColor` | `#000000` | Fundo da aplicação. |
| `secondaryBackgroundColor` | `#151515` | Superfícies secundárias. |
| `textColor` | `#FFFFFF` | Texto principal. |
| `font` | `Arial, Helvetica, sans-serif` | Família do conteúdo. |
| `headingFont` | `Arial, Helvetica, sans-serif` | Família dos títulos. |
| `baseFontSize` | `16` | Tamanho base em pixels. |
| `baseRadius` | `0.5rem` | Cantos dos componentes. |
| `buttonRadius` | `0.375rem` | Cantos dos botões. |
| `borderColor` | `#757575` | Limites de controles nativos. |

Validar os estados renderizados, especialmente a cor do texto dos botões. A tabela define o resultado visual desejado; não se deve presumir que toda combinação de versão e componente produza o contraste esperado sem inspeção.

As opções devem ser verificadas na versão de Streamlit fixada pelo projeto. Se uma opção não existir nessa versão, usar um ajuste visual localizado e documentado [3].

### 9.3 Componentes

| Necessidade | Recurso do Streamlit | Orientação |
| --- | --- | --- |
| Entrada conversacional | `st.chat_input` | Texto livre. No corpo principal, o componente pode ficar fixado na parte inferior [4]. |
| Mensagens | `st.chat_message` | Conteúdo do usuário e do sistema com nomes acessíveis [5]. |
| Progresso | `st.status` | Resumo da etapa real e detalhes expansíveis [6]. |
| Blocos visuais | `st.container` | Agrupar resultado e Impasse; usar chave estável quando necessário [7]. |
| Logo | `st.logo` ou imagem no cabeçalho | Escolher uma apresentação principal e evitar duplicação visual [8]. |
| Grafismo e CSS próprio | `st.html` | Conteúdo estático controlado pelo projeto [10]. |

Para imagens, ações, texto e divisões auxiliares, usar os componentes nativos correspondentes, conferindo as assinaturas na versão adotada.

Em `st.chat_message`, o parâmetro `name` define uma identificação acessível e não exibe automaticamente o nome na tela. Quando houver rótulo visível de interlocutor, renderizá-lo como texto dentro da mensagem [5].

### 9.4 Limites de customização

* Não montar uma página HTML completa dentro do Streamlit apenas para simular seus controles.
* Não criar botões HTML sem integração funcional com o estado da aplicação.
* Não interpolar mensagens do usuário ou conteúdo do modelo em HTML/CSS de confiança.
* Evitar seletores baseados em classes geradas dinamicamente. Preferir classes próprias e os pontos de personalização documentados.
* Quando usar uma chave de `st.container` para estilos, manter a chave estável; a documentação descreve a classe associada ao prefixo `st-key-` [7].
* Manter estilos localizados e revisar o resultado após atualização do Streamlit.
* Não remover contornos de foco, rótulos acessíveis ou mensagens úteis para obter uma aparência mais limpa.

### 9.5 Estado e reexecuções

O Streamlit reexecuta o script conforme as interações; o estado de sessão ajuda a preservar dados de interface entre essas execuções [11]. A persistência durável do fluxo pertence ao backend.

1. Renderizar mensagens e estados existentes sem iniciar novamente o trabalho dos agentes.
2. Associar cada envio e cada decisão do Impasse à execução correta.
3. Desabilitar ações enquanto a solicitação correspondente está em andamento.
4. Reutilizar a imagem já produzida; redesenhar a página não deve solicitar outra geração.
5. Recuperar a execução atual quando houver suporte de persistência; o frontend não deve prometer retomada que o backend ainda não oferece.

Idempotência e controle de versão são requisitos do fluxo de integração. Desabilitar um botão melhora a experiência, mas não substitui esses controles.

## 10. Responsividade e acessibilidade

| Faixa de largura | Comportamento |
| --- | --- |
| A partir de 1024 px | Cabeçalho compacto, abertura com arte à direita e conversa centralizada. |
| De 768 a 1023 px | Reduzir arte e espaçamentos; manter os blocos funcionais em uma coluna. |
| Abaixo de 768 px | Conteúdo em uma coluna, título menor, arte reduzida ou oculta e ações de Impasse empilhadas se necessário. |

Essas faixas são metas de layout do projeto, não uma afirmação sobre os pontos de quebra internos do Streamlit. Verificar a implementação real em cada largura.

* A interface deve funcionar a 360 px de largura, sem rolagem horizontal para executar as ações principais.
* O campo de chat não pode cobrir o final do resultado nem a decisão do Impasse.
* Texto e controles devem continuar utilizáveis com ampliação de 200%.
* Todas as ações precisam funcionar por teclado, com foco visível.
* Não comunicar status somente por cor; isso é especialmente importante para usuários com daltonismo.
* Imagens de resultado precisam de descrição textual; curvas decorativas não precisam de anúncio.
* Novos estados devem ser perceptíveis por tecnologia assistiva; verificar isso no aplicativo, sem presumir conformidade pela escolha dos componentes.

## 11. Organização sugerida para a implementação

Os caminhos abaixo indicam responsabilidades futuras. Somente `design.md` é entregue nesta etapa.

| Caminho sugerido | Responsabilidade |
| --- | --- |
| `design.md` | Fonte de referência das decisões visuais. |
| `.streamlit/config.toml` | Tema nativo e configurações visuais. |
| `app.py` | Entrada da aplicação Streamlit e composição das áreas. |
| `ui/styles.css` | Ajustes visuais centralizados e responsividade. |
| `ui/components.py` | Componentes reutilizáveis de marca, progresso, Impasse e resultado. |
| `assets/brand/` | Arquivos preparados do símbolo e do nome. |
| `assets/art/` | Grafismo decorativo original. |

Manter separadas as responsabilidades visuais e as regras dos agentes. Ajustes de cor, largura ou tipografia não devem exigir alterações no grafo.

## 12. Critérios de aceite visual

| ID | Critério verificável |
| --- | --- |
| VIS-01 | O fundo dominante é preto e a aplicação apresenta a marca Coxinh.IA corretamente. |
| VIS-02 | Branco, verde e grafismo em ciano/azul reproduzem a direção da referência sem inserir a marca Deloitte na interface. |
| VIS-03 | O estado inicial permite enviar uma mensagem imediatamente. |
| VIS-04 | O grafismo não encobre conteúdo nem permanece grande durante a conversa. |
| VIS-05 | Há uma hierarquia clara entre título, mensagens, progresso, decisão e resultado. |
| VIS-06 | Ações principais têm contraste adequado em repouso, foco e passagem do ponteiro. |
| VIS-07 | O Impasse apresenta motivos e as duas decisões de forma legível. |
| VIS-08 | Aprovação do Subchef, continuidade pelo usuário e parecer de consumo são distinguíveis. |
| VIS-09 | Reprovação, pendência e falha de avaliação não aparecem como consumo liberado. |
| VIS-10 | A imagem mantém a proporção e não é recriada por uma simples reexibição da página. |
| VIS-11 | A interface funciona em 360, 768 e 1440 px, com teclado e ampliação de texto. |
| VIS-12 | O significado dos estados permanece compreensível sem distinguir verde de vermelho. |
| VIS-13 | Nenhum status, contador, receita ou porcentagem demonstrativa é apresentado como dado real. |
| VIS-14 | A revisão visual cobre início, processamento, nova tentativa, Impasse, resultado, encerramento e falha de imagem. |

## 13. Referências

Consultadas em 14/11/2026. As imagens fornecidas orientam a direção visual; as fontes abaixo sustentam a paleta primária, os recursos técnicos e os critérios de contraste.

1. [Deloitte: paleta de cores publicada em material institucional](https://www2.deloitte.com/content/dam/Deloitte/sg/Documents/careers/sg-careers-deloitte-sg-50th-anniversary-art-competition-art-colour-palette.pdf).
2. [Streamlit: theming](https://docs.streamlit.io/develop/concepts/configuration/theming).
3. [Streamlit: referência de config.toml](https://docs.streamlit.io/develop/api-reference/configuration/config.toml).
4. [Streamlit: st.chat_input](https://docs.streamlit.io/develop/api-reference/chat/st.chat_input).
5. [Streamlit: st.chat_message](https://docs.streamlit.io/develop/api-reference/chat/st.chat_message).
6. [Streamlit: st.status](https://docs.streamlit.io/develop/api-reference/status/st.status).
7. [Streamlit: st.container](https://docs.streamlit.io/develop/api-reference/layout/st.container).
8. [Streamlit: st.logo](https://docs.streamlit.io/develop/api-reference/media/st.logo).
9. [W3C: WCAG 2.2, contraste mínimo](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).
10. [Streamlit: st.html](https://docs.streamlit.io/develop/api-reference/text/st.html).
11. [Streamlit: Session State](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state).
