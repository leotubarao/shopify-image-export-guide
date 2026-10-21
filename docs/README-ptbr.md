# Guia de exportação de imagens para Shopify

[English](../README.md)

Padrão para exportar e validar imagens de lojas Shopify sem perder nitidez nem cor, com bom peso para SEO e performance.

## O que tem aqui

| Arquivo | Para quem | O que é |
| --- | --- | --- |
| [`designers-guide-ptbr.md`](designers-guide-ptbr.md) | Designers (Photoshop) | Tamanhos em 2×, conversão para sRGB, configuração do Save for Web, nome de arquivo e checklist de envio |
| [`../shopify-image-optimizer/`](../shopify-image-optimizer/) | Designers e devs | Skill com o script que audita e otimiza as imagens antes de enviar ou subir na loja |

A versão principal, em inglês, está em [`../README.md`](../README.md) e [`designers-guide.md`](designers-guide.md).

## Baixar

- Com Git: `git clone https://github.com/leotubarao/shopify-image-export-guide.git`
- Sem Git: na página do repositório no GitHub, clique em **Code > Download ZIP** e extraia o arquivo.

Designers: o guia ([`designers-guide-ptbr.md`](designers-guide-ptbr.md)) mostra como exportar, e a skill confere os arquivos antes de enviar. Com o Claude não precisa de terminal: anexe as imagens numa conversa e peça para conferir para Shopify.

## Instalar a skill (opcional)

- **Claude (claude.ai ou app desktop):** a execução de código precisa estar ativada. Baixe o [`shopify-image-optimizer.zip`](https://github.com/leotubarao/shopify-image-export-guide/releases/latest/download/shopify-image-optimizer.zip) na última release, adicione em **Customize > Skills** e ative a skill. Em seguida, anexe imagens numa conversa e peça ao Claude para conferir ou otimizar para Shopify. Guia oficial (em inglês): [How to create custom skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills).
  - Se preferir montar o ZIP você mesmo, compacte a pasta `shopify-image-optimizer` de modo que a própria pasta seja a raiz do ZIP (`shopify-image-optimizer.zip` contendo `shopify-image-optimizer/SKILL.md`). Não compacte o repositório inteiro.
- **Claude Code:** copie a pasta `shopify-image-optimizer` para `~/.claude/skills/` (vale para todos os projetos) ou para `.claude/skills/` dentro de um projeto. Guia oficial (em inglês): [Extend Claude with skills](https://code.claude.com/docs/en/skills).
- **Sem Claude:** rode o script direto com Python, como mostrado abaixo.

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

O nome é opcional. Por padrão os arquivos só viram um slug (minúsculas, sem acento nem caractere especial, hífen no lugar de espaço). Para nomear pelo que aparece na imagem, peça ao Claude: a skill pergunta antes, olha cada imagem e monta o arquivo de nomes. Sem o Claude, preencha os nomes você mesmo (`--names-template names.json` e depois `--names names.json`). `--name-prefix` e `--name-suffix` colocam um texto antes ou depois de todos os nomes.

Toda otimização imprime um resumo de antes e depois: quantidade de imagens, peso total antes e depois, % economizado, cores convertidas para sRGB, arquivos renomeados e avisos. O `report.csv` traz os mesmos números por imagem (formato, dimensões, peso, perfil de cor e qualidade estimada, antes e depois).

O fluxo recomendado é rodar `--check` primeiro e só otimizar o que vier marcado FIX, de preferência a partir do arquivo original do designer, porque cada recompressão de JPEG perde um pouco de qualidade. Os relatórios CSV usam `;` como separador, então abrem direto no Excel em português.

## Pontos de atenção

- Os presets (tamanhos em 2× e pesos-alvo) são padrões da equipe, não limites da Shopify. Ajuste por cliente e por tema.
- A escala de qualidade do Photoshop não é a mesma da estimativa do `--check`. Confira o primeiro lote de cada designer e ajuste se a qualidade estimada vier abaixo de 80.
- O script foi testado com imagens sintéticas (fotos, CMYK com perfil, PNG transparente, nomes repetidos). Valide com arquivos reais de cliente antes de usar em lote.
