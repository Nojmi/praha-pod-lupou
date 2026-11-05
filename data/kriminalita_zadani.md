# Kriminalita jako vrstva a kritérium — zadání pro implementaci

## Zdroj dat
- Policie ČR, kriminalita.policie.gov.cz → „Ke stažení“ → záložka „Celá ČR (měsíce)“.
- Měsíční soubory `YYYYMM.geojson` (cca 20–27 MB, ČR celá), licence: lze šířit, vždy uvést zdroj (Policie ČR).
- Použitých 12 měsíců: 202511–202610. Doporučuji ale **vynechat poslední měsíc** (viz „Pasti“).
- Aktualizace: soubory se mění zpětně (stav deliktu se vyvíjí), stahovat pravidelně celé.

## Struktura
FeatureCollection, geometrie `Point` [lon, lat] (CRS84). Properties:
`id`, `mp` (bool, obecní policie), `date` (ISO), `state`, `relevance`, `types` (pole číselných ID).
Jeden delikt = jeden Feature, více typů v `types`.

## Číselníky
- `state`: 1 zjištěn pravděpodobný pachatel, 2 neobjasněno, 3 skutek se nestal, 4 skutek není trestným činem
- `relevance`: 1 nevybráno, 2 místo oznámení, 3 místo následku, 4 místo spáchání, 5 zahraniční lokalita, 6 chybná lokalita
- `types`: tabulka `types.csv` (id, parent_id1..3, name, label), 132 řádků. Hlavní třídy (parent_id1 = 0):

| id | třída | id | třída |
|---|---|---|---|
| 1 | Násilná | 63 | Obecně nebezpečná |
| 13 | Požáry, výbuchy | 79 | Dopravní nehody |
| 18 | Krádeže vloupáním | 80 | Toxikománie |
| 35 | Krádeže | 84 | Zbraně |
| 54 | Podvody | 96 | Extremismus |
| 55 | Jiná majetková | 97 | **Přestupky** |

Podtyp → hlavní třída: jít po `parent_id1` nahoru. Přestupky (97) se dělí na BESIP (74), alkohol a toxi (75), veřejný pořádek (76), majetek (77), ostatní (78).

## Důležité o poloze (readme od policie)
Souřadnice jsou **záměrně zkreslené**: obce jsou rozdělené na Voroného polygony (K-Means) a každý delikt dostane souřadnice středu své buňky. Body tedy NEJSOU adresy.
- V Praze je za měsíc cca 17–20 tisíc záznamů na ~1 900 unikátních bodů (za 12 měsíců ~3 300 včetně okolí).
- Hotspot na jednom bodě = jedna buňka, ne jedno místo. Nepoužívat heatmapu na body.
- Buňky nesedí s městskými částmi ani čtvrtěmi. Pro skóre agregovat buď po buňkách (Voroného vrstva), nebo přiřadit bod do polygonu městské části / čtvrti.

## Čištění
1. Prostorově oříznout na hranici Prahy (polygon MČ z Geoportálu Prahy, `TMMESTSKECASTI_P`, WGS 84). Hrubý obdélník (14.15–14.80, 49.90–50.25) zahrnuje i okolní obce.
2. Vyřadit `relevance` ∈ {5, 6}.
3. Vyřadit `state` ∈ {3, 4} (v Praze cca 2,9 %).
4. Nepoužít přímo `mp` jako filtr, jen jako informaci (obecní policie je v datech málo).

## Skóre bezpečnosti (kritérium)
- Vstupní třídy: **Násilná (1), Krádeže vloupáním (18), Krádeže (35), Podvody (54)**. Za 12 měsíců v Praze cca 23 700 záznamů (~1 800 měsíčně).
- Navržené váhy (k potvrzení uživatelem): násilná 3, vloupání 2, krádeže 1, podvody 0,5.
- Normalizace: počet / obyvatele jednotky (nebo na 1000 obyvatel). Potřeba počet obyvatel po MČ / čtvrtích (ČSÚ SLDB). Pozor, ve středu města (Praha 1) žije málo lidí a je tam hodně turistů, takže na obyvatele se centrum zkresluje; zvážit alternativu (na plochu nebo na „denní populaci“).
- Odhad stability: nápad je řídký, počítat přes ≥ 11–12 měsíců, ne po měsících.
- **Přestupky (97) a dopravní nehody (79) mimo skóre.** V Praze tvoří přestupky ~89 % záznamů, hlavně BESIP (rychlost, doprava), takže by skóre měřilo kontroly, ne kriminalitu. Jako volitelná samostatná vrstva: jen 76 (veřejný pořádek) a 75 (alkohol).

## Pasti
- **Poslední měsíc je neúplný:** říjen 2026 má jen 1 385 záznamů ve skóre-třídách oproti 1 770–1 996 v ostatních měsících (−25 %). Trestné činy se doplňují zpětně. Vynechat nebo vážit; jinak se čtvrti zdánlivě zlepší.
- Mravnostní činy (B), týrání a hospodářská kriminalita bez polohy se **nepublikují**; skóre je tedy neúplný obraz, v UI uvést.
- Stavy a typy se v čase mění, nepředpokládat stabilitu starších měsíců.

## Doporučený postup
1. Skript (Python), který stáhne/načte měsíční GeoJSON, vyfiltruje, namapuje `types` → hlavní třída.
2. Spatial join na polygon MČ/čtvrtí → agregace po jednotkách: počty po třídách a měsících.
3. Výstup do slim souboru (CSV/JSON po jednotkách, ~desítky kB), ne celé GeoJSONy do webu.
4. Vrstva: choropleth po MČ + volitelně Voroného buňky; kritérium: skóre na obyvatele s volitelnými vahami.
5. V UI uvést zdroj „Policie ČR, kriminalita.policie.cz“, datum stažení a upozornění na zkreslení poloh.