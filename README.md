# Praha pod lupou

Interaktivní mapa kvality bydlení v Praze: MHD (trasy a zastávky z PID), dostupnost a vybavenost
(školky, školy, obchody, lékaři, zeleň), docházkové zóny 5/10/15/30 min po skutečných cestách,
skóre místa s profily a váhami (rodina, senior, dojíždějící, vlastní), přepínač 2D/3D s budovami (výšky z OSM) a terénem (Copernicus DEM).

Aplikace je jedna samostatná HTML stránka (`index.html`, asi 10 MB), všechna data jsou vložená uvnitř.

## Rychlý start
    python3 build_app.py      # složí index.html z src/template.html a data/data8.json
    # pak otevři index.html v prohlížeči (3D potřebuje internet kvůli three.js z CDN)

## Struktura
- `src/template.html` – celá aplikace (2D canvas + 3D three.js), místo dat je `/*DATA*/`
- `data/data8.json` – hotová data (síť MHD, silnice, voda, zeleň, mřížky dostupnosti, graf cest, budovy, terén)
- `data/elevation.json` – výšky terénu (mřížka 600 m, Copernicus DEM přes Open-Meteo)
- `pipeline/` – skripty, kterými data vznikla (pořadí níže)
- `tools/dem_praha.py` – stažení výšek terénu

## Jak data vznikla (pipeline)
Vstupy do složky `raw/` (neverzovat, jsou velké): PID GTFS (https://pid.cz/o-systemu/opendata/) a OSM výřez
Prahy (BBBike, formát PBF). Skripty mají cesty napevno, před spuštěním je uprav.

1. `prep.py`, `build.py`, `build2.py`, `build3.py` – zastávky, hrany, tvary linek z GTFS
2. `osm.py`, `osm2.py` – silnice, řeky, voda z OSM
3. `amen.py`, `freq.py` – vybavenost, zeleň, spoje za hodinu
4. `build4.py` – mřížka 100 m s časy (dostupnost, vybavenost)
5. `graph.py` – pěší graf pro docházkové zóny
6. `bld.py`, `enc.py` – budovy a jejich výšky (kódování pro 3D)
7. `amen2.py` (střední a vysoké školy, hřiště, sportoviště, cyklostezky z OSM) a `extend.py` (doplní vrstvy do dat)
8. `crime.py` (kriminalita z Policie ČR, `data/kriminalita_praha_bunky_mesice.csv`, vrstva `krim`)
9. data8.json = výstup 1–7 + `dem` z `data/elevation.json`

## Souřadnice
Rovnoběžníkové zobrazení kolem 50,08 N, 14,42 E v metrech:
x = (lon − 14,42)·cos(50,08°)·111320, y = (lat − 50,08)·110574.

## Kriminalita
Zdroj: Policie ČR, kriminalita.policie.gov.cz (lze šířit, uvést zdroj). Jen násilná, vloupání, krádeže a podvody (váhy 3, 2, 1, 0,5), měsíce 202511 až 202609 (poslední měsíc je neúplný). Poloha je od policie zkreslená na střed Voroného buňky. Hodnota je pořadí oblasti (percentil) podle počtu na km², ne na obyvatele. Zadání: `data/kriminalita_zadani.md`.

## Známá omezení
- OSM výřez končí na 49,963–50,145 N, takže na severu a jihu Prahy chybí silnice, budovy a vybavenost.
- Výšky budov: 62 % z OSM (výška nebo počet pater × 3 m), zbytek odhad. Budovy jsou kvádry (LOD1).
- Terén je po 600 m, výšky po 90 m.
- Čas k vybavenosti v barevných plochách je vzdušná čára × 1,3 při 80 m/min, docházkové zóny jedou po cestách.

## Licence dat
© přispěvatelé OpenStreetMap (ODbL), PID (otevřená data), Copernicus DEM.
