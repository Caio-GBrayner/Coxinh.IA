# Coxinh.IA

Especificação de identidade visual e interface  
Versão 0.3.0 · 21/11/2026 · Português do Brasil

## 1. Experiência

O Coxinh.IA é um projeto de humor e sátira que transforma combinações improváveis em receitas de coxinha. A pessoa informa o que tem em mãos, acompanha a criação e pode voltar às receitas concluídas durante a mesma sessão.

O frontend será web, com estilos em CSS. A escolha do framework fica para a implementação. Os layouts podem ser desenhados enquanto o backend evolui, usando respostas simuladas para os estados ainda em integração.

## 2. Direção visual e marca

A referência principal é o TÒPAS. A abertura do Coxinh.IA usa a mesma ideia de profundidade entre letreiro, prato e objetos suspensos, com composição, marca e imagens estáticas próprias. A história usa a passagem de ilustração para fotografia como recurso editorial. [TÒPAS](https://bar-topas.ch/) · [Awwwards](https://www.awwwards.com/sites/topas#creator)

A grafia da marca é **Coxinh.IA**. Preservar a coxinha vazada branca e o ponto verde dos ativos existentes. Usar símbolo e nome no cabeçalho e o letreiro em grande escala na abertura. Os arquivos `Coxinh.IA marca.png`, `Coxinh.IA  logo nome.png` e `Coxinh.IA fachada.png` são referências de marca. `Coxinh.IA site.png` é referência para a apresentação das imagens da galeria.

| Cor | Valor | Uso |
| --- | --- | --- |
| Preto | `#000000` | Fundo da abertura e texto sobre o botão verde. |
| Branco | `#FFFFFF` | Texto sobre fundo escuro e superfícies claras, como a seção História. |
| Verde | `#86BC25` | Ponto da marca, ação principal e detalhes de destaque. |

Títulos grandes e condensados dão personalidade à abertura, à história e às receitas. A direção dos rascunhos combina fundos claros, fotografias em destaque, contornos finos e detalhes verdes em composições editoriais. Campos, preparo e estados usam uma família de leitura confortável, com texto direto. A fonte condensada fica concentrada nos títulos. Tipografia, escala de espaçamento e dimensões finais serão verificadas no layout responsivo.

## 3. Navegação

No cabeçalho, a marca fica à esquerda. O menu traz **Home**, **Suas receitas** e **História**. O botão verde **Criar receita** leva ao formulário da Home. **Suas receitas** leva à galeria e **História** à seção editorial logo abaixo da abertura.

## 4. Home e criação

No desktop, um card à esquerda reúne o título **“Crie sua Coxinha, seja criativo.”**, o campo de texto livre e o botão **Criar receita**. O campo permite descrever ingredientes, utensílios e meios de preparo. O formulário está disponível ao abrir a página.

À direita, uma coxinha com o recheio visível ocupa o primeiro plano. O letreiro **Coxinh.IA** aparece atrás dela. Imagens estáticas de objetos ficam distribuídas ao redor da coxinha. A sensação de que estão suspensos vem da posição, da escala e da sobreposição das imagens. A abertura usa composição 2D, com posições fixas. Modelos e renderização 3D ficam fora do escopo.

No celular, preservar a prioridade do título, do campo e do botão. Ajustar o enquadramento e reduzir a quantidade de objetos visíveis quando necessário.

### 4.1 Referências da composição

Os anexos orientam a escolha de **tijolo, madeira, rato, galinha, átomo, frasco de veneno e xícara de café**. Os objetos são decorativos e independentes do que a pessoa digita. Para a versão final, usar recortes com transparência real quando necessário. As prévias com fundo quadriculado ou marca d’água servem de referência visual.

A imagem da Deloitte fica como referência para a seção História. Na abertura, o letreiro é o do **Coxinh.IA**.

## 5. História

Logo abaixo da abertura, a seção **“Da Deloitte à Coxinh.IA”** apresenta um bloco editorial com título em grande escala, moldura fina preta, detalhe verde deslocado e uma fotografia de coxinha sobreposta à borda. O texto começa com uma frase em destaque sobre a origem no bootcamp e segue em poucos parágrafos, com largura confortável para leitura. O fundo claro sustenta o contraste com a abertura escura. O texto histórico final depende da revisão de João e Caio.

Em seguida aparecem a ilustração da turma e a foto real que serviu de base. Usar enquadramentos próximos e molduras com leves deslocamentos para relacionar as duas imagens ao rolar. No celular, empilhar os blocos e preservar títulos e texto inteiros.

A foto de João e Caio aparece no bloco **“A dupla por trás do Coxinh.IA”**, com título expressivo e moldura de fotografia. Os espaços reservados nos rascunhos representam as fotos que serão fornecidas. As fotos finais, a ilustração e o texto da história entram quando o material for selecionado.

## 6. Montagem

**Criar receita** inicia uma execução e abre a tela de montagem. A animação 2D é a mesma para todas as receitas. A massa recebe o recheio, fecha e toma a forma de coxinha. A montagem usa imagens fixas de massa e recheio como base para a sequência visual. O rascunho orienta uma composição escura, com o título grande **“Criando receita”**, a frase de ambientação e as camadas do preparo em destaque.

Enquanto a execução estiver em andamento, a interface pode alternar frases de ambientação como **“Calma que eu tô montando a coxinha”**. O estado funcional permanece explícito, por exemplo **“Criando receita”**. Mostrar uma etapa específica ou um método de preparo quando os dados da execução confirmarem essa informação. A transição para a receita pronta é comandada pelo retorno real do backend.

Se o fluxo entrar em impasse, a montagem dá lugar a um painel claro com contorno verde, título expressivo, motivos legíveis e as ações disponíveis. O título e os motivos devem descrever o estado recebido do backend. O motivo mostrado no rascunho é apenas um exemplo para estudo de composição. As decisões são aplicadas à execução atual. Na versão com movimento reduzido, uma imagem estática acompanha o estado textual.

## 7. Receita pronta

O resultado segue o tratamento editorial dos rascunhos, com uma fotografia grande e títulos condensados sobre fundo claro. No desktop, a imagem da coxinha fica à esquerda. À direita, apresentar título, subtítulo, ingredientes e modo de preparo. Utensílios e métodos podem aparecer junto ao preparo quando vierem na resposta. No celular, título e subtítulo aparecem primeiro, seguidos da imagem e dos detalhes.

**Aconselhamento de consumo** fica em um bloco próprio. Exibir o aviso, as ressalvas, a incerteza e os links de origem conforme os dados disponíveis. O bloco é informativo. Se o aconselhamento estiver pendente ou indisponível, comunicar esse estado em texto.

Se os dados da receita chegarem antes da imagem, apresentar o conteúdo disponível e reservar a área visual. Em caso de falha na imagem, manter a receita legível e informar a falha. Quando pronta, a imagem tem texto alternativo e identificação **Imagem gerada por IA**.

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

Na branch da etapa 7, `RecipeSession` inicia uma execução, consulta o estado e recebe a decisão de impasse. O histórico guarda os resultados concluídos pelo identificador da execução. A resposta final organiza os dados em `final_response.recipe` e `final_response.health`. O campo `image_prompt` descreve a imagem a gerar. [Sessão da receita](https://github.com/Caio-GBrayner/Coxinh.IA/blob/feat/cozinheiro-finalizacao/src/recipe_session.py) · [Finalização](https://github.com/Caio-GBrayner/Coxinh.IA/blob/feat/cozinheiro-finalizacao/src/graph/finalize.py)

Durante a integração, confirmar a interface de comunicação com o backend, o formato dos eventos de progresso se houver, os estados e campos finais de saúde e a entrega da imagem. A escolha de como sincronizar o histórico com uma imagem recebida depois faz parte dessa integração.

## 10. Revisão com UI UX Pro Max

Usar este documento como briefing para propor tipografia, espaçamento e hierarquia visual. A revisão deve cobrir a Home em desktop e celular, contraste, foco por teclado, legibilidade e movimento reduzido. A marca, a paleta, o conteúdo das seções e o fluxo descrito acima são as referências para avaliar as sugestões. [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)

## 11. Critérios de revisão

1. É possível localizar o formulário e iniciar a criação logo ao abrir a Home, em desktop e celular.
2. O letreiro, a coxinha e as imagens estáticas dos objetos deixam o card de criação legível e utilizável.
3. A ordem da história é texto, ilustração da turma, foto real e bloco da dupla.
4. A montagem reutiliza a mesma sequência visual e termina de acordo com o estado da execução.
5. O impasse consome a decisão na execução correta e deixa claras as ações disponíveis.
6. A receita é legível com a imagem pronta, pendente ou indisponível. O carrossel mostra foto ou imagem provisória, título e subtítulo em cada card.
7. O carrossel permite percorrer todas as receitas e retornar ao início, com setas, teclado e deslize. Verificar histórico vazio, uma receita e várias receitas, preservando o foco e o vínculo correto de cada card.
8. A moldura editorial da História mantém título, texto e fotos legíveis em desktop e celular.
9. A interface funciona com teclado, foco visível, ampliação de texto e preferência por movimento reduzido. Cada estado tem um rótulo textual.
10. O texto comum atende contraste mínimo de 4,5:1 e o texto grande, 3:1. [W3C, contraste mínimo](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
