# Guia de exportação de imagens para Shopify

[English](../README.md)

Padrão para exportar e validar imagens de lojas Shopify sem perder nitidez nem cor, com bom peso para SEO e performance.

## O que tem aqui

| Arquivo | Para quem | O que é |
| --- | --- | --- |
| [`designers-guide-ptbr.md`](designers-guide-ptbr.md) | Designers (Photoshop) | Tamanhos em 2×, conversão para sRGB, configuração do Save for Web, nome de arquivo e checklist de envio |
| [`../shopify-image-optimizer/`](../shopify-image-optimizer/) | Devs | Skill com o script que audita e otimiza as imagens entregues |

A versão principal, em inglês, está em [`../README.md`](../README.md) e [`designers-guide.md`](designers-guide.md).

## A regra em uma linha

Exportar em **2× a largura exibida**, em **sRGB**, em **JPEG qualidade 85** (nunca abaixo de 80), e controlar o peso **só pela qualidade**, nunca pelas dimensões.

## Usando o script

Requisitos: Python 3 e Pillow (`pip install Pillow`). Os comandos abaixo partem da raiz do repositório.

Auditar o que o designer entregou (não grava nada):

```bash
python3 shopify-image-optimizer/scripts/optimize.py pasta-do-designer --check --preset product
```

Otimizar sem perder resolução (os originais nunca são alterados):

```bash
python3 shopify-image-optimizer/scripts/optimize.py pasta-do-designer -o optimized --preset product
```

Presets: `product`, `collection`, `banner`, `blog`. Use `--display-width` para informar a largura real do espaço no tema e `--target-kb` para mudar o peso-alvo. Todas as opções estão em [`../shopify-image-optimizer/SKILL.md`](../shopify-image-optimizer/SKILL.md) (em inglês) ou em `--help`.

O fluxo recomendado é rodar `--check` primeiro e só otimizar o que vier marcado FIX, de preferência a partir do arquivo original do designer, porque cada recompressão de JPEG perde um pouco de qualidade. Os relatórios CSV usam `;` como separador, então abrem direto no Excel em português.

## Pontos de atenção

- Os presets (tamanhos em 2× e pesos-alvo) são padrões da equipe, não limites da Shopify. Ajuste por cliente e por tema.
- A escala de qualidade do Photoshop não é a mesma da estimativa do `--check`. Confira o primeiro lote de cada designer e ajuste se a qualidade estimada vier abaixo de 80.
- O script foi testado com imagens sintéticas (fotos, CMYK com perfil, PNG transparente, nomes repetidos). Valide com arquivos reais de cliente antes de usar em lote.
