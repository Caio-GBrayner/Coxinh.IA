# Coxinh.IA

Especificação de identidade visual e interface  
Versão 0.5.0 · 22/11/2026 · Português do Brasil

## 1. Experiência

O Coxinh.IA é um projeto de humor e sátira que transforma combinações improváveis em receitas de coxinha. A pessoa informa o que tem em mãos, acompanha a criação e pode voltar às receitas concluídas durante a mesma sessão.

O frontend será web, com estilos em CSS. Streamlit não faz parte desta interface. A escolha do framework fica para a implementação. Os layouts podem usar dados simulados durante a construção, mas seus estados e campos devem corresponder ao contrato real do backend.

## 2. Direção visual e marca

A referência principal é o TÒPAS. A abertura do Coxinh.IA usa a mesma ideia de profundidade entre letreiro, prato e objetos suspensos, com composição, marca e imagens estáticas próprias. A história usa a passagem de ilustração para fotografia como recurso editorial. [TÒPAS](https://bar-topas.ch/) · [Awwwards](https://www.awwwards.com/sites/topas#creator)

A grafia da marca é **Coxinh.IA**. Preservar a coxinha vazada branca e o ponto verde dos ativos existentes. Usar símbolo e nome no cabeçalho e o letreiro em grande escala na abertura. Os arquivos `Coxinh.IA marca.png`, `Coxinh.IA  logo nome.png` e `Coxinh.IA fachada.png` são referências de marca. `Coxinh.IA site.png` é referência para a apresentação das imagens da galeria.

| Cor | Valor | Uso |
| --- | --- | --- |
| Preto | `#000000` | Fundo da abertura e texto sobre o botão verde. |
| Branco | `#FFFFFF` | Texto sobre fundo escuro e superfícies claras, como a seção História. |
| Verde | `#86BC25` | Ponto da marca, ação principal e detalhes de destaque. |

Títulos grandes e condensados dão personalidade à abertura, à história e às receitas. A direção editorial do TÒPAS permanece na composição, nas sobreposições e no tratamento das imagens. O acabamento da interface busca a clareza e o cuidado de uma interface contemporânea da Apple: alinhamentos precisos, espaços generosos, superfícies simples, controles reconhecíveis, movimento discreto e resposta clara às ações. Não copiar componentes, cores ou identidade da Apple. Preservar o caráter irreverente da marca sem comprometer a leitura do formulário e da receita.

Manter um único sistema visual nas telas: a mesma lógica de tipografia, espaçamentos, alinhamento, raio de borda e estados dos controles. O primeiro enquadramento deve explicar visualmente o que a pessoa faz aqui, com o formulário utilizável sem rolagem no desktop. Nas demais seções, dar protagonismo a uma ideia por vez: a história privilegia texto e fotos; a montagem explica o processo; o resultado privilegia imagem e receita; o carrossel privilegia as criações. Não repetir o mesmo tipo de card e a mesma composição em todas as telas.

Campos, preparo e estados usam uma família de leitura confortável, com texto direto. A fonte condensada fica concentrada nos títulos. Usar detalhes verdes para orientar a atenção, evitando excesso de brilho, sombras, efeitos de vidro e animações simultâneas. Tipografia, escala de espaçamento e dimensões finais serão verificadas no layout responsivo.

## 3. Navegação

No cabeçalho, a marca fica à esquerda. O menu traz **Home**, **Suas receitas** e **História**. O botão verde **Criar receita** leva ao formulário da Home. **Suas receitas** leva à galeria e **História** à seção editorial logo abaixo da abertura.

## 4. Home e criação

No desktop, um card à esquerda reúne o título **“Crie sua Coxinha, seja criativo.”**, o campo de texto livre e o botão **Criar receita**. O campo permite descrever ingredientes, utensílios e meios de preparo. O formulário está disponível ao abrir a página.

À direita, uma coxinha com o recheio visível ocupa o primeiro plano. O letreiro **Coxinh.IA** aparece atrás dela. Quatro recortes estáticos flutuam ao redor: xícara de café, logo da Deloitte, silhueta de navio e símbolo isolado do Coxinh.IA. A sensação de suspensão vem da posição, escala, sobreposição e, se ajudar na leitura, de um movimento 2D sutil. Nenhum elemento depende dos ingredientes digitados. A abertura não usa modelos ou renderização 3D.

No celular, preservar a prioridade do título, do campo e do botão. Ajustar o enquadramento e reduzir a quantidade de objetos visíveis quando necessário. Objetos decorativos não recebem foco nem bloqueiam controles; o movimento respeita a preferência por movimento reduzido.

### 4.1 Referências da composição

Os quatro arquivos escolhidos estão em `docs/design/`:

| Elemento flutuante | Arquivo de referência |
| --- | --- |
| Xícara de café | `docs/design/cafe.jpg` |
| Logo da Deloitte | `docs/design/deloitte.jpg` |
| Silhueta de navio | `docs/design/navio.png` |
| Símbolo isolado do Coxinh.IA | `docs/design/Coxinh.IA marca.png` |

Esses caminhos identificam as referências visuais, não os ativos finais do frontend. Preparar recortes de produção com canal alfa real, bordas limpas e escala adequada para desktop e celular; a localização dos ativos finais será definida com a estrutura do frontend. Fundo branco, preto ou quadriculado gravado na imagem deve ser removido. Preservar o contorno e a grafia das marcas, sem redesenhá-las durante o recorte. Não usar versões com marca d’água como ativo final.

O letreiro grande continua sendo **Coxinh.IA**. A marca Deloitte é um elemento menor da composição e também faz a ponte visual com a seção História; o símbolo isolado do Coxinh.IA não substitui a assinatura completa do cabeçalho. Os demais objetos antes cogitados, como tijolo, rato e átomo, deixam de integrar esta composição.

## 5. História

Logo abaixo da abertura, a seção **“Da Deloitte à Coxinh.IA”** apresenta um bloco editorial com título em grande escala, moldura fina preta, detalhe verde deslocado e uma fotografia de coxinha sobreposta à borda. O texto começa com uma frase em destaque sobre a origem no bootcamp e segue em poucos parágrafos, com largura confortável para leitura. O fundo claro sustenta o contraste com a abertura escura. O texto histórico final depende da revisão de João e Caio.

Em seguida aparecem a ilustração da turma em `docs/design/turma_ilustrada.png` e a foto real que serviu de base em `docs/design/turma_bootcamp.png`. Usar enquadramentos próximos e molduras com leves deslocamentos para relacionar as duas imagens ao rolar. No celular, empilhar os blocos e preservar títulos e texto inteiros.

A foto de João e Caio aparece no bloco **“A dupla por trás do Coxinh.IA”**, com título expressivo e moldura de fotografia. A foto da dupla ainda será selecionada; o espaço reservado no rascunho representa esse ativo pendente.

## 6. Montagem

**Criar receita** inicia uma execução e abre a tela de montagem. A animação 2D é a mesma para todas as receitas. A massa recebe o recheio, fecha e toma a forma de coxinha. A montagem usa imagens fixas de massa e recheio como base para a sequência visual. O rascunho orienta uma composição escura, com o título grande **“Criando receita”**, a frase de ambientação e as camadas do preparo em destaque.

Enquanto a execução estiver em andamento, a interface pode alternar frases de ambientação como **“Calma que eu tô montando a coxinha”**. O estado funcional permanece explícito, por exemplo **“Criando receita”**. Mostrar uma etapa específica ou um método de preparo quando os dados da execução confirmarem essa informação. A transição para a receita pronta é comandada pelo retorno real do backend.

A sequência de montagem serve para explicar visualmente a criação enquanto a execução acontece. Ela pode repetir ou permanecer em um quadro de espera caso o backend demore, sem sugerir porcentagem ou etapa técnica inventada. Quando o backend terminar, concluir a transição e exibir o resultado. Um estado textual de processamento permanece visível também quando a animação estiver desativada.

Se o fluxo entrar em impasse, a montagem dá lugar a um painel claro com contorno verde, título expressivo, motivos legíveis e as ações disponíveis. O título e os motivos devem descrever o estado recebido do backend. O motivo mostrado no rascunho é apenas um exemplo para estudo de composição. As decisões são aplicadas à execução atual. Na versão com movimento reduzido, uma imagem estática acompanha o estado textual.

## 7. Receita pronta

O resultado segue o tratamento editorial dos rascunhos, com uma fotografia grande e títulos condensados sobre fundo claro. No desktop, a imagem da coxinha fica à esquerda. À direita, apresentar título, subtítulo, ingredientes e modo de preparo. Utensílios e métodos podem aparecer junto ao preparo quando vierem na resposta. No celular, título e subtítulo aparecem primeiro, seguidos da imagem e dos detalhes.

**Aconselhamento de consumo** fica em um bloco próprio, com a imagem de um personagem fictício de médico ao lado do texto. A imagem funciona como recurso narrativo da sátira, sem nome, registro profissional, instituição ou aparência de endosso médico real. O conteúdo e as fontes devem permanecer legíveis sem a imagem. Exibir aviso, contraindicações, incerteza e links de origem conforme os dados disponíveis. O bloco é informativo e não usa selos como “seguro” ou “aprovado para consumo”. Se o aconselhamento estiver pendente, insuficiente ou indisponível, comunicar o estado em texto.

Se os dados da receita chegarem antes da imagem, apresentar o conteúdo disponível e reservar a área visual. Em caso de falha na imagem, manter a receita legível e informar a falha. Quando pronta, a imagem tem texto alternativo e identificação **Imagem gerada por IA**.

### 7.1 Geração da imagem da receita

O `image_prompt` do Cozinheiro descreve a receita final para o provedor de imagem. A escolha inicial para experimentar a integração é **Recraft V4.1 Flash V2 (free)**, acessado pelo OpenRouter. A variante gratuita está anunciada para retirada em **28/11/2026**; por isso o modelo é provisório e a troca de provedor não pode exigir mudanças na apresentação ou no fluxo da receita. Não encaminhar automaticamente a chamada para uma variante paga. Se não houver provedor gratuito disponível, exibir a receita com imagem provisória e o estado de imagem correspondente.

O backend integrado ainda utiliza um provedor simulado. Uma referência simulada não deve ser apresentada como fotografia real gerada. Quando a integração com um provedor real existir, validar se a imagem respeita a massa, o recheio e a descrição visual; guardar na sessão a referência utilizável pela interface.

## 8. Suas receitas

A Home reúne as receitas concluídas em um **carrossel horizontal infinito**. Cada card traz **foto, título e subtítulo**, com imagem grande e hierarquia editorial de cardápio. Ao avançar além da última receita, o carrossel volta à primeira. Ao recuar além da primeira, volta à última. A ordem inicial começa pela receita mais recente.

Setas visíveis permitem avançar e voltar no desktop e no celular. Também aceitar deslize no celular e navegação por teclado nos controles. Como comportamento inicial, o avanço ocorre por interação da pessoa. O clique em um card abre a receita completa. Ao voltar ao carrossel, preservar a posição de leitura.

No desktop, distribuir vários cards conforme a largura disponível. No celular, mostrar um card principal e parte do próximo para indicar continuidade. Com uma única receita, apresentar apenas seu card. Com o histórico vazio, apresentar a mensagem definida abaixo. A repetição visual usada pelo carrossel mantém o mesmo identificador de receita e um único registro no histórico. A implementação deve preservar o foco e expor apenas uma versão acessível de cada card quando usar cópias para fechar o ciclo.

Uma nova receita entra no início da sequência sem interromper uma interação em curso. Quando faltar a foto, o card mantém o título e o subtítulo com uma imagem provisória. Respeitar a preferência de movimento reduzido nas transições.

O histórico inicial vive em memória na sessão da aplicação. Uma nova criação usa sua própria execução, e as receitas anteriores da mesma sessão continuam disponíveis. Ao encerrar o processo da aplicação, as receitas em memória são perdidas. Antes da primeira criação, apresentar **“Suas criações aparecem aqui.”**

## 9. Estados e integração

| Estado | Comportamento da interface |
| --- | --- |
| Campo vazio | Manter o formulário disponível e indicar o campo a preencher. |
| Processando | Mostrar montagem e estado textual. Evitar envios repetidos enquanto a solicitação correspondente estiver em andamento. |
| Aguardando decisão | Mostrar o motivo do impasse e as ações disponíveis, como **Continuar criação** ou **Encerrar**, conforme o fluxo. |
| Concluída | Mostrar a resposta final e disponibilizar a receita no histórico. |
| Imagem pendente ou com falha | Manter o conteúdo da receita disponível e comunicar o estado da imagem na área reservada. |
| Falha de execução ou encerramento | Identificar o estado e apresentar a ação de recuperação quando estiver disponível. |

Na `main`, `RecipeSession` inicia uma execução, consulta seu estado e recebe a decisão de impasse. O histórico registra resultados concluídos pelo identificador da execução. A resposta final organiza `final_response.recipe`, `final_response.health` e `final_response.image`, incluindo `image.status` e `image.url`. O campo `image_prompt` descreve a imagem a gerar. [Sessão da receita](https://github.com/Caio-GBrayner/Coxinh.IA/blob/main/src/recipe_session.py) · [Finalização](https://github.com/Caio-GBrayner/Coxinh.IA/blob/main/src/graph/finalize.py)

Antes da implementação da interface, definir como ela chama `RecipeSession`, como preserva a mesma sessão e o `thread_id` ao navegar ou atualizar a página, e se haverá eventos reais de progresso. Frases de ambientação não devem simular etapas técnicas não observadas. A busca web do agente de saúde está integrada; a ferramenta homônima do MCP é opcional e o servidor padrão ainda não a registra. Não depender dela para exibir o aviso.

## 10. Referências de execução e revisão

As referências abaixo servem como métodos de trabalho durante a etapa 11. Este documento e as decisões de marca, fluxo e conteúdo feitas pela dupla têm prioridade quando alguma sugestão automática propuser uma direção diferente. Não é necessário instalar todas as ferramentas para começar o layout; escolher as que forem úteis quando houver uma interface concreta para avaliar.

| Referência | Aplicação no Coxinh.IA |
| --- | --- |
| [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | Explorar combinações de tipografia, espaçamento e hierarquia compatíveis com a marca e verificar o layout responsivo. |
| [Impeccable](https://github.com/pbakaus/impeccable) | Fazer uma revisão por seção: primeiro composição, tipos e espaçamentos; depois crítica visual, acessibilidade, adaptação a telas e acabamento. Tratar apontamentos automáticos como achados para inspeção, não como mudanças obrigatórias. |
| [Skills de Emil Kowalski](https://github.com/emilkowalski/skills) | Definir a função de cada movimento antes da implementação: ambientação na abertura, explicação na montagem, continuidade no carrossel e resposta às ações. Preferir CSS para movimento predeterminado e só adicionar controle mais complexo se a interação exigir. |
| [Taste Skill](https://github.com/Leonxlnx/taste-skill) | Planejar cada seção com uma ideia e um elemento visual dominante; usar os ativos reais do projeto e validar a composição no navegador em larguras diferentes. Seu padrão genérico de cores, textos ou navegação não substitui o briefing do Coxinh.IA. |

### 10.1 Movimento e interação

| Área | Função do movimento | Diretriz |
| --- | --- | --- |
| Abertura | Dar profundidade à composição editorial. | Uma entrada discreta do letreiro, coxinha e recortes pode ocorrer ao carregar. A flutuação 2D dos recortes é decorativa, sutil e não deve competir com o formulário. |
| História | Relacionar a ilustração às fotografias. | Usar uma transição curta quando as imagens entrarem na leitura, preservando enquadramento e legibilidade sem depender de efeitos para contar a história. |
| Montagem | Explicar a montagem e comunicar espera. | Repetir a sequência fixa durante o processamento; o estado textual real permanece presente. O fim da animação não declara que a receita terminou. |
| Carrossel | Mostrar continuidade entre receitas. | A transição acompanha setas e deslize, pode ser interrompida por nova interação e não avança sozinha. Preservar posição, foco e identificador ao retornar da receita. |
| Formulário e botões | Confirmar ações. | Foco sempre visível; resposta visual breve ao pressionar. Transições de controles não atrasam o envio nem escondem erros. |

Preferir propriedades como transformação e opacidade para movimento, reaproveitando os mesmos tempos e curvas definidos no código. Não adicionar biblioteca de animação para um efeito que o CSS resolva. Interações frequentes devem responder imediatamente. Animações decorativas param ou são substituídas por uma apresentação estática quando a pessoa preferir movimento reduzido; ações e estados continuam compreensíveis sem movimento. [Princípios de animação](https://github.com/emilkowalski/skills/blob/main/skills/animate/SKILL.md)

### 10.2 Conferência visual

Antes de encerrar a implementação de cada tela, verificar no navegador ao menos desktop, tablet e celular, inclusive em larguras próximas de 1440, 1024, 768 e 390 pixels. Conferir recortes, texto longo, títulos inesperados da IA, resultado sem imagem, histórico vazio e carregamento. Inspecionar se o conteúdo é legível com teclado, texto ampliado e movimento reduzido. Os critérios da seção 11 são a referência para aceitar a tela. [Taste Skill](https://github.com/Leonxlnx/taste-skill/blob/main/skills/taste-skill/SKILL.md) · [Princípios de design da Apple](https://developer.apple.com/design/human-interface-guidelines/design-principles)

## 11. Critérios de revisão

1. É possível localizar o formulário e iniciar a criação logo ao abrir a Home, em desktop e celular.
2. O letreiro, a coxinha e os quatro recortes com transparência real deixam o card de criação legível e utilizável em desktop e celular.
3. A ordem da história é texto, ilustração da turma, foto real e bloco da dupla.
4. A montagem reutiliza a mesma sequência visual e termina de acordo com o estado da execução.
5. O impasse consome a decisão na execução correta e deixa claras as ações disponíveis.
6. A receita é legível com a imagem pronta, pendente ou indisponível. Uma referência simulada ou uma falha não é exibida como fotografia real. O carrossel mostra foto ou imagem provisória, título e subtítulo em cada card.
7. O carrossel permite percorrer todas as receitas e retornar ao início, com setas, teclado e deslize. Verificar histórico vazio, uma receita e várias receitas, preservando o foco e o vínculo correto de cada card.
8. A moldura editorial da História mantém título, texto e fotos legíveis em desktop e celular.
9. A interface funciona com teclado, foco visível, ampliação de texto e preferência por movimento reduzido. Cada estado tem um rótulo textual.
10. O texto comum atende contraste mínimo de 4,5:1 e o texto grande, 3:1. [W3C, contraste mínimo](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
11. O personagem fictício acompanha o aconselhamento sem sugerir credencial ou endosso médico real; aviso, incerteza e fontes continuam compreensíveis sem a imagem.
