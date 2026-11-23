# Textos fixos da interface do Coxinh.IA

Texto editorial da etapa 11.0. Este arquivo é a referência para os textos escritos pela equipe. Título, subtítulo, ingredientes, preparo, aviso de saúde e fontes de cada receita vêm da execução e não são textos fixos. Ao implementar o frontend, centralizar estes textos em um único lugar no código e revisar este documento caso mudem.

## Navegação e abertura

| Local | Texto |
| --- | --- |
| Marca | Coxinh.IA |
| Navegação | Home · Suas receitas · História |
| Título do formulário | Crie sua Coxinha, seja criativo. |
| Rótulo do campo | O que vai na sua coxinha? |
| Ajuda do campo | Conte seus ingredientes, utensílios e como imagina o preparo. |
| Botão principal | Criar receita |
| Campo vazio | Conte sua ideia para criar uma receita. |

## História

**Título:** Da Deloitte à Coxinh.IA

**Abertura:** Tudo começou com o tamanho da coxinha da padaria do Moinho. Na turma do bootcamp, ela virou assunto recorrente e motivo de piada. João e Caio já tinham outra brincadeira: transformar qualquer ideia em um sistema de IA.

**Continuação:** As duas brincadeiras se encontraram. Por que não criar um sistema capaz de inventar coxinhas com qualquer combinação que alguém imaginar? A ideia virou um jeito de praticar o que a dupla estudava no bootcamp da Deloitte e construir um projeto de verdade. Assim nasceu o Coxinh.IA.

**Imagens na ordem editorial:** ilustração da turma em `docs/design/turma_ilustrada.png`; foto real correspondente em `docs/design/turma_bootcamp.png`; retrato da dupla em `docs/design/dupla.png`, abaixo de “João & Caio”. As duas primeiras imagens mostram o mesmo grupo, com enquadramentos correspondentes.

**Legenda da foto da dupla:** Imagem criada por IA, a dupla ainda não tirou uma foto real...

**Bloco da dupla:** A dupla por trás do Coxinh.IA

**Texto da dupla:** João e Caio têm o hábito de perguntar se uma ideia daria um sistema de IA. A coxinha da padaria do Moinho deu. Juntos, transformaram a piada da turma em um projeto para experimentar, aprender e construir uma aplicação de verdade.

O texto conta a origem informada por João. A referência ao bootcamp situa o encontro das ideias; ela não atribui à Deloitte a criação, o patrocínio ou a aprovação do Coxinh.IA. A dupla ainda revisará a redação antes da publicação.

## Montagem e Impasse

| Estado | Texto fixo |
| --- | --- |
| Processando | Criando receita |
| Frase de ambientação 1 | Calma, estamos montando a coxinha. |
| Frase de ambientação 2 | A ideia já está na cozinha. |
| Frase de ambientação 3 | Essa combinação vai render uma história. |
| Impasse | Precisamos da sua decisão para continuar. |
| Campo de orientação | O que você quer ajustar? |
| Adição de ingrediente | Adicionar ingrediente |
| Salvar ajuste | Salvar orientação |
| Retomar após salvar | Continuar criação |
| Encerrar | Encerrar criação |

As frases de ambientação não representam etapas reais do grafo. No Impasse, exibir também a crítica e os dados que vierem da execução. **Salvar orientação** permanece na pausa; **Continuar criação** retoma o fluxo. Os rótulos devem acompanhar apenas as ações realmente disponíveis no estado atual.

## Receita, saúde e histórico

| Local ou estado | Texto fixo |
| --- | --- |
| Cabeçalho do resultado | Sua coxinha está pronta |
| Seção de ingredientes | Ingredientes |
| Seção de preparo | Modo de preparo |
| Seção de saúde | Aconselhamento de consumo |
| Fontes do aconselhamento | Fontes consultadas |
| Incerteza do aconselhamento | O que ainda não sabemos |
| Crédito da imagem real | Imagem gerada por IA |
| Galeria | Suas receitas |
| Histórico vazio | Suas criações aparecem aqui. |
| Imagem indisponível | A receita está pronta, mas não conseguimos gerar a imagem. |
| Imagem pendente | A imagem da receita ainda está sendo preparada. |
| Aconselhamento indisponível | Não foi possível consultar o aviso de saúde. |
| Falha geral | Não foi possível concluir esta criação. Tente novamente. |
| Conflito de atualização | Essa receita foi atualizada em outro momento. Confira a versão atual antes de continuar. |

Não apresentar uma referência `simulated://` como foto gerada. O bloco de saúde usa o texto e as fontes que o fluxo devolver e não exibe selo de segurança ou aprovação para consumo. A mensagem de erro geral só deve oferecer nova tentativa quando a aplicação conseguir fazê-la sem repetir uma ação já confirmada.
