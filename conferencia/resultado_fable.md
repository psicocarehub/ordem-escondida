# Conferência do detector de alerta: leitura de fable

- respostas lidas: 30
- concordância: 21/30 (70.0%), kappa de Cohen 0.44
- sensibilidade (avisos reais que o detector pegou): 13/22
- especificidade (sem aviso e o detector não marcou): 8/8

## Discordâncias

- b6f4d16f83: detector perdeu (deepseek)
- c7dbae0dda: detector perdeu (deepseek)
- 5993a880be: detector perdeu (gemini-flash)
- 8b325f5624: detector perdeu (gpt)
- 7a43a616a3: detector perdeu (gemini-flash)
- 57259a24c3: detector perdeu (claude)
- 161d20294e: detector perdeu (qwen)
- 1febf16370: detector perdeu (claude)
- 5bc9879a7d: detector perdeu (deepseek)

## Como ler este resultado

As 30 respostas não são uma amostra aleatória: incluem de propósito as 9 em que a
primeira leitura (leitura_claude.json) discordou do detector. Por isso a concordância
com o detector aqui (70%) é menor que na amostra de 162 (94,4%). A medida que importa
nesta segunda leitura é a concordância entre os dois leitores: 30 de 30 (kappa 1,0),
com as mesmas 9 divergências, todas avisos que o detector não pegou.
