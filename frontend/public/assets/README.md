# Ativos da interface

Uso das referências de café, navio e marca Deloitte autorizado por João nesta implementação, em 22/11/2026. Originais em `docs/design/` preservados. Não foram encontradas marcas d'água visíveis nos originais utilizados. Não há alegação de patrocínio ou endosso da Deloitte.

| Arquivo | Origem e tratamento | Situação |
| --- | --- | --- |
| `coxinh-symbol.png` | `Coxinh.IA marca.png`, recorte com imagegen | Alfa verificado no navegador; refinamento de bordas e fidelidade exata do contorno ainda exigem revisão. |
| `coffee-cutout.png` | `cafe.jpg`, recorte com imagegen | Alfa verificado; revisão final de bordas pendente. |
| `deloitte-cutout.png` | `deloitte.jpg`, remoção do quadriculado com imagegen | Alfa verificado; conferir fidelidade tipográfica antes do aceite. O suporte branco na tela é CSS. |
| `ship-cutout.png` | `navio.png`, recorte com imagegen | Alfa verificado; conferir geometria antes do aceite. O suporte verde na tela é CSS. |
| `coxinha-hero.png` | Composição decorativa nova produzida com imagegen | Alfa verificado. É ilustração fotográfica decorativa; não corresponde a uma receita executada. Aprovação visual final pendente. |
| `turma-ilustrada.png` | Cópia de `turma_ilustrada.png` | Imagem fornecida no projeto, sem alteração. |
| `turma-bootcamp.png` | Cópia de `turma_bootcamp.png` | Imagem fornecida no projeto, sem alteração. |

Não foram inventadas fotos da dupla ou do personagem de saúde. Essas duas fotos permanecem pendentes. Nenhum desses ativos decorativos é usado para representar a imagem final de uma receita.

## Prompts utilizados

Ferramenta: imagegen integrada, com `transparent_background=true`. Os resultados selecionados foram copiados para esta pasta. Os candidatos de segunda tentativa não substituíram os selecionados porque não trouxeram melhoria clara.

- Símbolo: “Edit this exact existing Coxinh.IA brand symbol. Remove ONLY the black background, including interior black hole, to true alpha transparency. Preserve precisely the existing white hollow coxinha contour and green dot, proportions, edges and colors. No redraw, no text, no new elements. Crop canvas to symbol with small padding. Production website transparent PNG asset.”
- Café: “Production transparent PNG cutout. Remove only the white background to true alpha. Keep the exact coffee cup and saucer, no changes, clean edges, no shadow outside object.”
- Deloitte: “Production transparent PNG cutout. Remove the baked checkerboard background to true alpha. Preserve exact black Deloitte wordmark and its period. Do not redraw or change letterforms. Crop with small padding.”
- Navio: “Production transparent PNG cutout. Remove only white background including window holes to true alpha. Keep exact black ship silhouette geometry. Crop with small padding.”
- Coxinha: “Create a photorealistic editorial food cutout for a Brazilian coxinha recipe web app, isolated on genuinely transparent alpha background. One large golden breaded coxinha sliced in half showing moist shredded chicken and a little parsley, the front half leaning lightly toward viewer, with one whole coxinha slightly behind. Three quarter camera view, warm natural studio light, crisp delicious crumb texture. No plate, no props, no lettering, no logo, no background, no watermark. Objects fill the canvas with clean edge and small padding. This is a generic decorative hero asset, not a photograph of a user's generated recipe.”

A presença de alfa foi testada por pixels transparentes e quase opacos (alfa ≥ 250); a existência de canal alfa não substitui a inspeção das bordas nem certifica que uma operação generativa preservou cada pixel de uma marca.
