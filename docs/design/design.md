# Coxinh.IA

Especificação de identidade visual e interface  
Versão 0.5.0 · 22/11/2026 · Português do Brasil

## 1. Experiência

O Coxinh.IA é um projeto de humor e sátira que transforma combinações improváveis em receitas de coxinha. A pessoa informa o que tem em mãos, acompanha a criação e pode voltar às receitas concluídas no carrossel global.

O frontend será web, com estilos em CSS. Streamlit não faz parte desta interface. A escolha do framework fica para a implementação. Os layouts podem usar dados simulados durante a construção, mas seus estados e campos devem corresponder ao contrato real do backend.

## 2. Direção visual e marca

A referência principal é o TÒPAS. A abertura do Coxinh.IA usa a mesma ideia de profundidade entre letreiro, prato e objetos suspensos, com composição, marca e imagens próprias. Os objetos flutuam suavemente, com controle de pausa e respeito à preferência por movimento reduzido. A história usa a passagem de ilustração para fotografia como recurso editorial. [TÒPAS](https://bar-topas.ch/) · [Awwwards](https://www.awwwards.com/sites/topas#creator)

Ajuste solicitado em 22/11/2026: usar o arquivo original `Coxinh.IA  logo nome.png` no cabeçalho e no rodapé; Archivo expandida (125%, peso 800) nos títulos da História e da dupla, com Source Sans 3 nos parágrafos. A turma ocupa uma única moldura: ao rolar para baixo, a fotografia revela-se da esquerda para a direita sobre a ilustração; ao subir, o movimento reverte. Com movimento reduzido, ambas aparecem sem transição. A identidade preta, branca e verde permanece.

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

A foto `dupla.png` aparece abaixo do nome **João & Caio** no bloco **“A dupla por trás do Coxinh.IA”**, em uma moldura quadrada que preserva os dois retratados. Em telas estreitas, o nome, a foto e o texto ficam empilhados.

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

O backend usa OpenRouter quando configurado e simulação sem chave. Uma referência simulada não deve ser apresentada como fotografia real gerada. Quando a integração com um provedor real existir, validar se a imagem respeita a massa, o recheio e a descrição visual; guardar a referência utilizável na API persistente.

## 8. Suas receitas

A Home reúne as receitas concluídas em um **carrossel horizontal infinito**. Cada card traz **foto, título e subtítulo**, com imagem grande e hierarquia editorial de cardápio. Ao avançar além da última receita, o carrossel volta à primeira. Ao recuar além da primeira, volta à última. A ordem inicial começa pela receita mais recente.

Setas visíveis permitem avançar e voltar no desktop e no celular. A passagem entre receitas acontece pelas setas; a rolagem vertical da página não altera a seleção. O clique em um card abre a receita completa. Ao voltar ao carrossel, preservar a posição de leitura.

No desktop, distribuir vários cards conforme a largura disponível. No celular, mostrar um card principal e parte do próximo para indicar continuidade. Com uma única receita, apresentar apenas seu card. Com o histórico vazio, apresentar a mensagem definida abaixo. A repetição visual usada pelo carrossel mantém o mesmo identificador de receita e um único registro no histórico. A implementação deve preservar o foco e expor apenas uma versão acessível de cada card quando usar cópias para fechar o ciclo.

Uma nova receita entra no início da sequência sem interromper uma interação em curso. Quando faltar a foto, o card mantém o título e o subtítulo com uma imagem provisória. Respeitar a preferência de movimento reduzido nas transições.

O carrossel é global, aprovado por João. SQLite preserva receitas e impasses entre reinícios; o modo opcional em memória perde os dados ao encerrar. Antes da primeira criação, apresentar **“As receitas concluídas da cozinha aparecem aqui.”**

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

A interface usa `docs/CONTRATO_API.md` e `src/api/app.py`: POST retorna 202 e polling acompanha `running` até estado terminal ou Impasse. O ID ativo é preservado na aba. Frases de ambientação não simulam etapas técnicas não observadas. A pesquisa de saúde continua responsabilidade do backend.

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
| Carrossel | Mostrar continuidade entre receitas. | A transição acompanha somente as setas, não muda com a rolagem vertical e não avança sozinha. Preservar posição, foco e identificador ao retornar da receita. |
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
7. O carrossel permite percorrer todas as receitas e retornar ao início pelas setas, sem avançar pela rolagem da página. Verificar histórico vazio, uma receita e várias receitas, preservando o foco e o vínculo correto de cada card.
8. A moldura editorial da História mantém título, texto e fotos legíveis em desktop e celular.
9. A interface funciona com teclado, foco visível, ampliação de texto e preferência por movimento reduzido. Cada estado tem um rótulo textual.
10. O texto comum atende contraste mínimo de 4,5:1 e o texto grande, 3:1. [W3C, contraste mínimo](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
11. O personagem fictício acompanha o aconselhamento sem sugerir credencial ou endosso médico real; aviso, incerteza e fontes continuam compreensíveis sem a imagem.

## 12. Aplicação da etapa 11

Esta especificação descreve a experiência e a direção visual. Os comportamentos verificáveis estão em [`requirements.md`](requirements.md), e a sequência de trabalho está em [`tasks.md`](tasks.md). [`conteudo_interface.md`](conteudo_interface.md) concentra os textos fixos. A etapa usa o frontend React com TypeScript e Vite em `frontend/`, com estilos CSS próprios, e a API FastAPI em `src/api/app.py` já preparada nesta branch. O Codex deve conferir os arquivos reais antes de modificar o contrato; não criar uma segunda API, outra implementação do histórico ou uma segunda fonte divergente para os textos.

### 12.1 Composição e ativos finais

| Região | Implementação visual | Ativos e limite |
| --- | --- | --- |
| Cabeçalho | Assinatura Coxinh.IA acompanhada de “by” e do logotipo Deloitte em escala menor; Home, Suas receitas, História e ação de criar. | Usar `coxinh-logo-nome.png` e o recorte transparente `deloitte-cutout.png` dos ativos de produção do frontend. O logo Deloitte mantém contraste em uma pequena base branca. |
| Abertura | Card de criação à esquerda; letreiro gigante atrás de uma coxinha aberta à direita. Profundidade por escala e sobreposição. | Usar uma fotografia de coxinha própria ou devidamente autorizada, separada das imagens geradas para as receitas. O recorte precisa ter bordas limpas e canal alfa. |
| Elementos suspensos | Xícara, marca Deloitte, navio e símbolo Coxinh.IA em quatro posições distintas, afastados do formulário. | `cafe.jpg`, `deloitte.jpg`, `navio.png` e `Coxinh.IA marca.png` são referências em `docs/design/`. Converter em ativos de produção antes de exibir. Não usar quadriculado, fundo branco gravado ou marca d'água. Não redesenhar os logotipos. |
| História | Moldura editorial, título de grande escala e sequência ilustração da turma → foto da turma; foto de João e Caio abaixo dos nomes. | `turma_ilustrada.png`, `turma_bootcamp.png` e `dupla.png` em `frontend/public/assets/`. |
| Receita | Imagem à esquerda no desktop e conteúdo à direita; no celular, título e subtítulo antes da imagem. | Imagem real vinda da API apenas se utilizável; estados simulados, pendentes e falhos recebem composição provisória com texto. |
| Saúde | Bloco separado da receita com foto de um personagem fictício de médico, expressivo e claramente cenográfico. | A foto do personagem ainda não foi escolhida. A apresentação do aconselhamento deve funcionar sem ela e sem sugerir orientação de um profissional real. |

Os ativos preparados para o navegador devem ficar em uma pasta explícita dentro de `frontend/`, com nomes legíveis e referências únicas no código. Conferir tamanho, nitidez, transparência e autorização de uso antes de integrá-los. Enquanto faltar um recorte aprovado, manter a composição funcional e registrar a pendência; não colocar uma versão com marca d'água para preencher espaço.

### 12.2 Estados visuais ligados ao contrato

O formulário envia texto livre para `POST /api/recipes`. Durante a espera, a montagem mostra o estado textual **Criando receita** e uma sequência 2D fixa, sem percentual ou alegação de evento do grafo. O retorno `completed` abre o resultado, `awaiting_user` abre o Impasse e `cancelled` apresenta encerramento. Falha de rede ou do servidor aparece com ação de recuperação consciente: jamais repetir automaticamente uma criação ou uma decisão cujo resultado possa já ter sido aceito.

O Impasse mostra a crítica recebida, proposta quando existir, orientações e ingredientes já registrados. **Salvar orientação** usa a versão atual, mantém a pausa e não solicita uma nova receita. **Continuar criação** retoma o mesmo `thread_id`; **Aceitar receita como está** envia a decisão `accept` sem incluir campos do formulário não salvos e encaminha a proposta atual diretamente ao Cozinheiro, sem nova rodada do SubChef; **Encerrar criação** encerra o mesmo fluxo. Aceitar só fica disponível quando há uma proposta. Depois do Cozinheiro, a execução mantém aconselhamento de consumo, imagem e finalização. Conflito de versão exige consultar o estado atual e mostrar o que já foi salvo, preservando os dados ainda digitados.

A API fornece `/images/<arquivo>` ou null; o frontend valida nomes simples PNG/JPG/JPEG/WebP/SVG e compõe a URL com o endereço da API. O proxy local remove `/api`; imagens são globais, com fallback para simulação, recurso indisponível ou falha de carregamento.

O histórico mostra resumos globais de resultados concluídos, começa pela receita mais recente na apresentação e mantém o mesmo ID de cada card ao navegar. O carrossel volta ao começo ou ao fim pelas setas, sem avançar pela rolagem vertical. A abertura de um card consulta `GET /recipes/{id}` e revela o resultado completo dessa execução. Voltar preserva a posição no carrossel.

### 12.3 Revisão com as referências de design

Usar **UI UX Pro Max** para examinar hierarquia, tipografia e layout responsivo; **Impeccable** para criticar composição, espaçamento e acabamento; as orientações de **Emil Kowalski** para reduzir o movimento ao que esclarece estado e ação; e **Taste Skill** para manter direção visual própria e conferir o resultado no navegador. Aplicar apenas achados que melhorem esta especificação. As referências não impõem nova paleta, novos textos, dependências ou estética genérica. Conferir visualmente Home, História, montagem, Impasse, resultado e galeria em desktop, tablet e celular, também com títulos longos, ausência de imagem, teclado e preferência por movimento reduzido.
