# russo-pt

Converte texto russo (cirílico) em sílabas que um falante de português consegue ler em voz alta e que soam próximas do russo.

```
$ python3 russo_pt.py "спаси+бо"
spa-SSÍ-ba
```

Só precisa de Python 3, sem dependências.

## Uso

```
python3 russo_pt.py "Москва́ спаси́бо"     # texto direto
python3 russo_pt.py -f texto.txt          # arquivo
echo "хорошо́" | python3 russo_pt.py      # entrada padrão
python3 russo_pt.py                       # modo interativo
```

Marque a vogal tônica com acento agudo (а́) ou com `+` logo depois dela (`спаси+бо`). Ela muda o som das outras vogais: o "o" fraco vira "a", o "e" fraco vira "i". Palavras de uma sílaba e palavras com ё não precisam de marca.

## Exemplo

[`exemplos/hino_urss.txt`](exemplos/hino_urss.txt) tem o hino da União Soviética com as tônicas marcadas:

```
$ python3 russo_pt.py -f exemplos/hino_urss.txt
sa-IÚS ni-ru-CHY-myi ris-PÚ-blik sva-BÓD-nyrr
spla-TÍ-la na-VIÉ-ki vi-LÍ-ka-ia rus.
da ZDRÁS-tvu-it SÓZ-dan-nyi VÓ-lii na-RÓ-daf
i-DÍ-nyi, ma-GÚ-tchii sa-VIÉT-skii sa-IÚS!
...
```

## Como ler o resultado

| Escrita | Som |
|---|---|
| `MAIÚSCULAS` | sílaba tônica, com acento na vogal (sa-IÚS) |
| `rr` | "r" raspado de garganta, como o "r" carioca de "rato" (х) |
| `r` | "r" batido de "caro", sempre, mesmo no começo da palavra |
| `y` | "i" com a língua puxada para trás (ы) |
| `lh`, `nh` | "l" e "n" suaves (ль, нь), como em "olho" e "ninho" |
| `ch` / `chch` | "ch" de "chá" (ш) / "ch" mais longo e chiado (щ) |
| `tch`, `ts` | como em "tchau" (ч) e "tsunami" (ц) |
| `ss` | sempre "s" de "sapo", nunca "z" |

## Dica

Quando uma palavrinha como на, по ou за leva a tônica, junte-a à palavra seguinte: `на+берег` sai `NÁ-bi-rik`, como se canta em "Катюша".
