# Rozmístění kešek po Česku: data a výpočty

Podklady pro mapu `lov/index.html`: kolik kešek je potřeba, aby to lidé měli blízko, a kolik práce dá je rozmístit.

## Zdroje dat

| Soubor | Co obsahuje | Zdroj |
|---|---|---|
| `data/raw/pop2026.json` | počet obyvatel k 1. 1. 2026 za 6 258 obcí (kód obce → počet), celkem 10 915 839 | ČSÚ, datová sada OBY02A „Počet obyvatel podle pohlaví“, ukazatel 2406P, otevřená data `data.csu.gov.cz` |
| `data/raw/ruian/obce_*.json.gz` | hranice obcí, zjednodušené zhruba na 150 m | RÚIAN, ČÚZK, mapová služba `Prohlizeci_sluzba_nad_daty_RUIAN`, vrstva 12 |
| `data/raw/ruian/vo_*.json.gz` | hranice 14 556 volebních okrsků, zjednodušené zhruba na 80 m | RÚIAN, vrstva 20 |
| `data/raw/am_stats.json` | počet adresních míst v každém volebním okrsku | RÚIAN, vrstva 1, spočítáno na serveru |
| `data/raw/cz_border_naturalearth.json` | obrys Česka | Natural Earth 1:10m přes balíček `world-atlas@2.0.2` |

Data ČSÚ a ČÚZK jsou otevřená data, při dalším použití uveď zdroj.

## Jak výpočet funguje

1. **`scripts/place_area.py`**: rozmístění „podle území“. Kešky se rozprostřou po obrysu Česka a pak se posouvají k nejvzdálenějším místům, aby nejhorší vzdálenost byla co nejmenší. Výstup `data/out/places_area.json`.
2. **`scripts/build_grid.py`**: mapa obyvatelstva. Obyvatele každé obce rozdělí do jejích volebních okrsků podle počtu adresních míst (u okrsků bez adres podle plochy) a okrsky rozpočítá do čtverců 0,5 × 0,5 km. Vytvoří taky obrys republiky z hranic obcí a seznam 40 největších měst.
3. **`scripts/place_pop.py`**: rozmístění „podle obyvatel“ pro 77, 206, 300, 1 200, 2 000, 2 500 a 3 000 kešek. Hustota kešek roste s odmocninou hustoty obyvatel a část váhy zůstává venkovu. Počítá podíl lidí do 1, 2, 3 a 5 km, vzdálenost pro 95 % a 99 % lidí a nejvzdálenější bod. Výstup `data/out/place.json`.
4. **`scripts/labor.py`**: pracnost rozmístění 1 200 kešek pro týmy 1–600 lidí. Každý má svou oblast (k-means), objíždí kešky metodou nejbližšího souseda, 12 minut na kešku, 25 km/h ve městě a 45 km/h mimo něj, silnice = 1,35 × vzdušná čára. Výstup `data/out/labor.json`.
5. **`scripts/embed.py`**: zapíše výsledky do `../index.html` (bloky `CZ`, `POP`, `WORST`, `PLACES` a tabulku pracnosti).

## Spuštění

```bash
pip install -r requirements.txt
./fetch.sh   # volitelné: stáhne čerstvá data (potřebuje přístup k data.csu.gov.cz a ags.cuzk.gov.cz)
./run.sh     # přepočítá data/out a aktualizuje ../index.html, trvá zhruba 15 minut
```

Pro jiný rok počtu obyvatel spusť `YEAR=2027 ./fetch.sh`. Mřížka obyvatelstva (`S.npy`, `W.npy`, asi 7 MB) se do repa neukládá, `run.sh` ji pokaždé vytvoří znovu v dočasné složce.

## Omezení

- Adresní místa nejsou totéž co obyvatelé: zahrnují i chaty a firmy, takže v rekreačních oblastech mohou lidi mírně nadhodnocovat.
- Vzdálenosti jsou vzdušnou čarou. Jízda v `labor.py` je odhad z průměrné rychlosti, ne ze skutečné silniční sítě.
- Rozmístění nezná terén ani konkrétní bezpečná místa a výsledek závisí na náhodném startu (pevné `seed`), takže při jiném seedu se čísla mohou lišit v desetinách.
