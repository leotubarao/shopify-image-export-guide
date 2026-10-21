# Guia de exportação de imagens para a loja (Photoshop → Shopify)

[English](designers-guide.md)

Exporte em 2× a largura exibida, em sRGB e em JPEG com qualidade 85. Assim a imagem chega nítida na Shopify e leve o bastante para SEO e velocidade. Nunca reduza as dimensões para baixar o peso: reduza só a qualidade, e só até 80.

## Por que a imagem perde qualidade na loja

1. **Poucos pixels.** Celulares e monitores 4K exibem a imagem com o dobro de pixels. Um arquivo de 1.200 px num espaço de 1.200 px fica borrado: ele precisa ter 2.400 px.
2. **Perfil de cor errado.** A Shopify remove o perfil de cor ao exibir a imagem na loja. Um arquivo em Adobe RGB, Display P3 ou CMYK sai com cor opaca ou trocada. Converta para sRGB antes de exportar.
3. **Compressão demais.** A Shopify não comprime no upload, mas a imagem pode ser comprimida ao ser entregue pelo tema e é convertida para WebP ou AVIF quando o navegador aceita. JPEG exportado com qualidade baixa piora nessa etapa. Quanto melhor o arquivo enviado, melhor o resultado final.

Arquivo pesado demais também prejudica: atrasa a página e o SEO. Por isso a regra é dimensão correta e peso controlado só pela qualidade de compressão.

## Tamanhos por tipo de imagem

Exporte com o dobro da largura em que a imagem aparece no tema. Os valores abaixo são o padrão; o dev informa a largura real de cada espaço em cada cliente.

| Tipo | Exibida no tema (exemplo) | Exportar (2×) | Proporção | Peso-alvo |
| --- | --- | --- | --- | --- |
| Produto | 1.000 a 1.200 px | 2.048 a 2.400 px no maior lado | 1:1, igual em todas as fotos | até 500 KB |
| Coleção | 1.000 px | 2.000 px | a do tema, igual em todas | até 400 KB |
| Banner / hero em largura total | 1.600 px | 3.200 px | a do tema | até 900 KB |
| Blog | 1.200 px | 2.400 px | a do tema | até 500 KB |

Limites da Shopify: 20 MB e 20 megapixels por imagem. Para produto quadrado, a Shopify indica 2.048 × 2.048 px como o tamanho que costuma exibir melhor. Nunca amplie uma arte pequena no Photoshop: peça o arquivo original. Abaixo de 800 px o zoom da página de produto pode não funcionar.

## Passo a passo no Photoshop

Os nomes de menu estão em inglês, com a versão em português entre parênteses; podem variar conforme a versão do Photoshop.

1. **Parta do PSD original**, em alta resolução. Exporte sempre dele, nunca de um JPEG já exportado: cada nova compressão perde qualidade.
2. **Defina o tamanho final** em Image > Image Size (Imagem > Tamanho da imagem). Largura em px = 2× o valor da tabela. Ao diminuir, use Resample: Bicubic Sharper (reduction). Se a arte for menor que o necessário, não amplie: avise o dev.
3. **Confira o modo** em Image > Mode: RGB Color e 8 Bits/Channel. Nunca CMYK.
4. **Converta para sRGB** em Edit > Convert to Profile (Editar > Converter em perfil): Destination Space = sRGB IEC61966-2.1, Intent = Relative Colorimetric, Use Black Point Compensation ligado. Use *Convert*, não *Assign*: só o Convert muda os valores das cores.
5. **Exporte** em File > Export > Save for Web (Legacy) (Arquivo > Exportar > Salvar para Web (Legado)), atalho Alt+Shift+Ctrl+S no Windows e Opt+Shift+Cmd+S no Mac. Use a configuração da próxima seção.
6. **Confira o peso** no canto inferior esquerdo da janela, com o preview em 100%. Acima do peso-alvo, baixe a qualidade de 5 em 5, até no mínimo 80. Se ainda passar, não reduza as dimensões: envie o arquivo ao dev.
7. **Nomeie o arquivo** para SEO: minúsculas, hífens, sem acento nem espaço, descrevendo a imagem. Exemplo: `serum-vitamina-c-frente.jpg` e `serum-vitamina-c-textura.jpg`. Evite "final", "novo" e "copia".
8. **Fundo transparente:** exporte PNG-24 com Transparency ligado. O dev converte para WebP se ficar pesado.

## Configuração do Save for Web (Legacy)

A equipe toda usa este método e esta configuração, para a escala de qualidade ser a mesma entre os arquivos.

| Campo | Valor | Por quê |
| --- | --- | --- |
| Formato | JPEG | Melhor relação entre peso e qualidade para fotos |
| Quality | 85, nunca abaixo de 80 | Faixa "Very High" do Photoshop, adequada para foto de produto |
| Progressive | Ligado | A imagem aparece inteira e vai ganhando nitidez |
| Optimized | Ligado | Arquivo menor, sem perder qualidade |
| Convert to sRGB | Ligado | Garante as cores certas, já que a Shopify remove o perfil |
| Embed Color Profile | Tanto faz | O que vale é a conversão do passo 4 |
| Blur | 0 | Qualquer valor acima tira a nitidez |
| Metadata | None | Remove EXIF e miniaturas, que só pesam |
| Image Size | 100% (largura e altura já definidas no passo 2) | Não redimensione de novo aqui |
| Matte | White | Só importa se a arte tiver áreas transparentes |

Se algum campo tiver nome diferente na sua versão, mande um print da janela ao dev. A alternativa Export As (Exportar como) também serve: ligue Convert to sRGB, escolha Metadata = None e não deixe o programa redimensionar. A escala de Quality do Export As pode não equivaler à do Save for Web, então o dev confere o primeiro lote antes de a equipe adotar esse método.

## Checklist antes de enviar

- [ ] Largura igual a 2× a da tabela (por exemplo, 2.400 px para produto)
- [ ] Modo RGB, 8 bits, convertido para sRGB com Convert to Profile
- [ ] JPEG com Quality 85 (mínimo 80), Progressive e Optimized ligados, Metadata em None
- [ ] Peso dentro da meta da tabela, sem ter reduzido as dimensões
- [ ] Nome em minúsculas, com hífens, sem acento e sem espaço
- [ ] Proporção igual à das outras imagens do mesmo grupo (produtos em 1:1)
- [ ] Exportado do PSD original, não de outro JPEG
- [ ] Preview em 100% com texto de rótulo e bordas nítidos, sem blocos nem halos

## Conferência do dev

Antes de subir na Shopify, o dev roda a skill [`shopify-image-optimizer`](../shopify-image-optimizer/SKILL.md) em modo de auditoria. Ela lista, por arquivo, formato, dimensões, peso, perfil de cor, qualidade JPEG estimada e nome, e marca OK ou FIX sem alterar nada.

```
python3 shopify-image-optimizer/scripts/optimize.py pasta-do-designer --check --preset product
```

Arquivo com qualidade estimada abaixo de 80, dimensão menor que o 2× ou perfil fora do sRGB volta ao designer para nova exportação do PSD. Arquivo com dimensão e cor corretas, mas acima do peso, o dev otimiza sem reduzir a resolução:

```
python3 shopify-image-optimizer/scripts/optimize.py pasta-do-designer -o optimized --preset product
```

## Fontes

- [Shopify: tipos de mídia do produto](https://help.shopify.com/en/manual/products/product-media/product-media-types): formatos aceitos, limite de 20 MB e tamanho de 2.048 × 2.048 px para produto quadrado.
- [Shopify: imagens do tema](https://help.shopify.com/en/manual/online-store/images/theme-images): sem compressão no upload, remoção do perfil de cor na exibição, limites de 20 MB e 20 megapixels.
- [Adobe Community: opções do Export As](https://community.adobe.com/t5/photoshop-ecosystem-discussions/i-need-help-understanding-the-options-in-export-as-quot/m-p/12762940): Convert to sRGB e Embed color profile.
- [Adobe Community: cores erradas ao exportar sRGB](https://community.adobe.com/t5/photoshop-ecosystem-discussions/ps-export-as-srgb-jpg-colors-wrong/m-p/14432944): perfil do documento e Convert to sRGB.

O que não vem dessas páginas: a regra do 2× e as metas de peso são recomendações da equipe, não limites da Shopify. As duas páginas da Shopify divergem no limite de megapixels (20 numa, 25 noutra); este guia usa o menor. Os campos do Save for Web seguem a interface padrão do Photoshop, e não encontrei página da Adobe acessível que confirme cada um.
