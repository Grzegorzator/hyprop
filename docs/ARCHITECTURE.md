# HyProp — Architektura programu
**Hybrid Rocket Preliminary Sizing & Analysis Environment**
Wersja 0.2 (Etap 0 — po recenzji współautora, 10 rozszerzeń + warstwa `physics/`)
2026-07-15 · autorzy: MASSLACZEK12 + Claude

---

> **Zmiany 2026-10 (v0.2, przed integracją z YAADO)** — ten dokument opisuje
> projekt v0.1; obowiązują poniższe odstępstwa:
>
> * **GUI usunięte** (`hyprop/gui`, instalatory, skróty). HyProp to biblioteka
>   do sizingu; docelowo solver napędu hybrydowego w YAADO (MDO).
> * Usunięte rekordy `database/` (żadnych prób ogniowych jeszcze nie było);
>   moduł `hyprop.database` pozostaje jako API.
> * **D11 (nowe): sprawności.** Ciąg wg konwencji współczynników korekcyjnych
>   Suttona (9th ed., r. 3.5, równ. 3-40/3-41): `F = η_c*·η_noz·ṁ·c_i`,
>   `c_i = v_e + (p_e − p_a)·ε·c*_i/p_c`. W v0.1 η_c* obniżało tylko Pc
>   (jak w HRAP), przez co ∂F/∂η_c* < 0.
> * **D12 (nowe): γ.** `StationState.gamma` = zamrożone cp/cv (wszystkie
>   backendy), `gamma_eq` = γ_s równowagowe (CEA GAMMAs).
> * **Dysza w sizingu**: ε z rozprężania CEA (p_e = p_a na wysokości
>   projektowej), Cf dostarczony = λ·η·Cd·Cf_i.
> * `simulation.cea_backend` jest respektowany (wcześniej solver zawsze
>   używał Cantery).
> * Walidacja: `validation/` + `docs/VALIDATION.md`.

## 1. Cel i zakres

Środowisko inżynierskie do projektowania hybrydowych silników rakietowych: od wymagań
misji, przez sizing, symulację czasową (logika HRAP), wyznaczanie reprezentatywnych
punktów pracy (ROP), analizy wrażliwości i niepewności, po optymalizację, raporty
i GUI. Docelowo rozszerzalne o modele 1D, erozję dyszy, CFD, OpenMDAO.

Ustalenia z Etapu 0:

* Termochemia: **RocketCEA (główny) + Cantera (fallback)** za wspólnym interfejsem.
* Lokalizacja: `D:\Claude\HYBRID\HYBRID\hyprop\`.
* Kolejność: **core → walidacja → GUI** (GUI PySide6 na stabilnym API).
* Język: kod/docstringi EN, komunikacja i raporty PL.
* Recenzja v0.1: dodano `physics/`, analizy bezwymiarowe/wrażliwości/niepewności,
  logging, wersjonowany config, rejestr pluginów, batch mode, `database/`,
  Python API, specyfikację raportu NASA-style.

## 2. Zasady projektowe

1. **Fizyka za interfejsami.** Każdy model fizyczny (zbiornik, wtryskiwacz, regresja,
   geometria, dysza, termochemia) implementuje klasę abstrakcyjną (ABC). Wymiana modelu
   = wymiana klasy, bez zmian w solverze.
2. **`physics/` jako jedyne źródło równań.** Wszystkie równania ogólne (gazodynamika,
   termodynamika, przepływ ściśliwy, wymiana ciepła, transport) żyją w warstwie
   `physics/`, która **nie importuje niczego z pozostałych modułów** (zależność
   jednokierunkowa: moduły → physics). Zero duplikacji wzorów.
3. **API-first.** GUI i CLI to tylko klienci publicznego API (`hyprop.run(config)`).
   Każda funkcjonalność musi być osiągalna skryptowo, bez GUI.
4. **Jednostki SI + Pint.** Warstwa wejścia/wyjścia używa `pint`; rdzeń numeryczny
   liczy na floatach SI (wydajność), konwersja na granicach modułów.
5. **Brak magic numbers.** Stałe w `core/constants.py` z jednostką i źródłem.
6. **Każde równanie udokumentowane** — docstring: wzór, założenia, źródło
   (Sutton & Biblarz, Humble, Karabeyoglu, HRAP Theory, NASA CEA RP-1311, ESDU 91022...).
7. **Konfiguracja deklaratywna i wersjonowana.** Cały przypadek = `EngineConfig`
   (pydantic) z polem `version`; loader migruje starsze wersje → kompatybilność wstecz.
8. **ROP jako obowiązkowy koncentrator.** Moduły projektowe (dysza, sizing, analiza
   cieplna, raporty, optymalizacja) pobierają parametry wyłącznie z `oppoints`,
   nigdy z pojedynczego kroku symulacji.
9. **Rejestr pluginów.** Nowe modele (regresja, geometria, zbiornik, wtryskiwacz,
   backend CEA) umieszczone we właściwych katalogach są wykrywane i rejestrowane
   automatycznie (dekorator `@register_model` + skan pakietu) — solver i GUI widzą
   je bez modyfikacji kodu.
10. **Pełna obserwowalność.** Centralny `logging` (DEBUG/INFO/WARNING/ERROR),
    opcjonalny zrzut całego przebiegu solvera (iteracje Pc, zbieżność, eventy)
    do pliku — do debugowania i do załącznika raportu.

## 3. Struktura pakietu

```
hyprop/
├── pyproject.toml            # zależności, entry-points, konfiguracja narzędzi
├── hyprop/
│   ├── api.py                # ★ publiczne API: run(config), run_batch(cases),
│   │                         #   size(mission), optimize(problem) — GUI/CLI to klienci
│   ├── core/                 # fundament
│   │   ├── constants.py      #   stałe fizyczne (g0, R_u...) z jednostkami i źródłami
│   │   ├── units.py          #   rejestr Pint, dekoratory konwersji SI
│   │   ├── config.py         #   EngineConfig (pydantic, pole version, migracje)
│   │   ├── state.py          #   SimulationState / TimeHistory (wektory wyników)
│   │   ├── registry.py       #   rejestr pluginów: @register_model + autodiscovery
│   │   ├── logging.py        #   konfiguracja loggera, zrzut przebiegu solvera
│   │   └── exceptions.py     #   hierarchia wyjątków domenowych
│   ├── physics/              # ★ wspólna biblioteka równań (bez zależności od reszty)
│   │   ├── gas_dynamics.py   #   relacje izentropowe, fale, przepływ w kanałach
│   │   ├── compressible.py   #   A/A*, Ma(A), przepływ krytyczny, Cf ideal
│   │   ├── thermodynamics.py #   równowaga faz, politropy, bilanse energii, EOS-y
│   │   ├── heat_transfer.py  #   konwekcja (Bartz), przewodzenie, promieniowanie
│   │   ├── combustion.py     #   entalpie tworzenia, bilanse O/F, teoria Marxmana
│   │   └── transport.py      #   lepkość, przepływy dwufazowe, kryteria kawitacji
│   ├── data/                 # wbudowane bazy właściwości (YAML, tylko-odczyt)
│   │   ├── oxidizers/        #   N2O (ESDU 91022 / CoolProp), LOX, GOX, HTP, custom
│   │   ├── fuels/            #   HTPB, parafina, HDPE, ABS, PMMA, custom
│   │   └── validation/       #   prusak_v2 (HRAP CSV), przypadki z literatury
│   ├── database/             # ★ baza użytkownika (zapisywalna, wersjonowana)
│   │   ├── engines/          #   zapisane projekty silników (EngineConfig + wyniki)
│   │   ├── materials/        #   materiały konstrukcyjne (grafit, stale, kompozyty)
│   │   ├── injectors/        #   scharakteryzowane wtryskiwacze (Cd, geometrie)
│   │   └── tests/            #   dane z prób ogniowych (do kalibracji a, n, Cd, eta)
│   ├── cea/                  # termochemia
│   │   ├── backend.py        #   ThermochemistryBackend (ABC): query(of, Pc, eps) →
│   │   │                     #   CEAResult(Tc, gamma, M, c*, Isp, Cp, Cv, R, skład,
│   │   │                     #   właściwości: komora/gardziel/wylot)
│   │   ├── rocketcea_backend.py
│   │   ├── cantera_backend.py
│   │   ├── native_cea.py     #   (przyszłość) generacja .inp / parser .out CEA2
│   │   └── cache.py          #   cache + interpolacja tablic (of, Pc, eps) — szybkość
│   ├── regression/           # modele regresji paliwa (plugin: @register_model)
│   │   ├── base.py           #   RegressionModel (ABC): rdot(G, ...) [m/s]
│   │   ├── power_law.py      #   rdot = a·G^n (warianty G_ox / G_total, człon L^m)
│   │   └── (przyszłość: Marxman z physics/combustion, korekty, erozja)
│   ├── geometry/             # geometria ziarna (plugin)
│   │   ├── base.py           #   GrainGeometry (ABC): A_port(w), A_burn(w), D_h(w),
│   │   │                     #   V_fuel(w), perimeter(w);  w = grubość spalona
│   │   ├── cylindrical.py    #   pojedynczy port
│   │   ├── multiport.py      #   N portów kołowych
│   │   ├── wagon_wheel.py
│   │   ├── star.py
│   │   └── custom.py         #   port z konturu użytkownika (offset konturu)
│   ├── tank/                 # modele zasilania utleniaczem (plugin)
│   │   ├── base.py           #   TankModel (ABC): step(dt, mdot_out) → stan zbiornika
│   │   ├── equilibrium_blowdown.py  # samoprężny N2O, równowaga term. (HRAP)
│   │   ├── pressure_fed.py   #   stałe ciśnienie (butla / prasowanie)
│   │   └── constant_mdot.py  #   uproszczony (do sizingu wstępnego)
│   ├── injector/             # (plugin)
│   │   ├── base.py           #   InjectorModel (ABC): mdot(P1, P2, stan płynu)
│   │   ├── spi.py            #   Single-Phase Incompressible
│   │   ├── nhne.py           #   Dyer NHNE (prototyp: 08_injector_model_NHNE.py)
│   │   └── hem.py            #   Homogeneous Equilibrium Model
│   ├── chamber/              # komora spalania
│   │   └── sizing.py         #   V_c, L, D, L/D, L*, czas rezydencji, pre/post-komora
│   ├── nozzle/
│   │   ├── sizing.py         #   D_t, D_e, eps optymalne dla wybranego ROP
│   │   └── losses.py         #   strata rozbieżności (stożek/dzwon), eta_noz
│   │                         #   (przepływ: physics/compressible.py)
│   ├── performance/
│   │   └── metrics.py        #   F, Isp, c*, Cf, eta_c*, eta_Cf, eta_overall
│   ├── simulation/           # serce programu — logika HRAP
│   │   ├── solver.py         #   pętla czasowa, sprzężenie zbiornik↔wtryskiwacz↔
│   │   │                     #   komora↔regresja↔dysza; iteracja Pc w każdym kroku
│   │   ├── events.py         #   detekcja: LRO, burnout, wyczerpanie paliwa, zgaśnięcie
│   │   └── timestep.py       #   sterowanie krokiem (stały / adaptacyjny)
│   ├── oppoints/             # ★ Representative Operating Points (moduł centralny)
│   │   ├── averaging.py      #   metody: time, thrust-weighted (domyślna),
│   │   │                     #   mdot-weighted, qdot-weighted, Pc-weighted, custom
│   │   ├── design_points.py  #   Peak Performance, Impulse-Weighted, Heat Load,
│   │   │                     #   Mass Flow, Median Impulse, percentyle impulsu
│   │   ├── phases.py         #   fazy: ciekła / przejściowa / gazowa + statystyki
│   │   └── report_data.py    #   struktura wyników ROP dla raportu/GUI/modułów
│   ├── sizing/               # projekt odwrotny: wymagania misji → geometria
│   │   └── preliminary.py    #   F, It, tb, h, Pa, Isp_min, SF → D_t, ziarno, zbiornik
│   ├── batch/                # ★ tryb wsadowy
│   │   ├── matrix.py         #   generacja macierzy przypadków (siatka / LHS / lista)
│   │   └── runner.py         #   równoległe wykonanie (multiprocessing), agregacja
│   │                         #   wyników do DataFrame, checkpointing
│   ├── optimization/
│   │   ├── problem.py        #   zmienne/cele/ograniczenia nad EngineConfig
│   │   ├── scipy_driver.py   #   minimize / differential_evolution
│   │   └── nsga2_driver.py   #   pymoo (NSGA-II, wielokryterialna)
│   ├── analysis/
│   │   ├── plots.py          #   wykresy (F, Pc, O/F, Isp, c*, γ, T, mdot, port,
│   │   │                     #   regresja, skum. It, wagi, histogramy) + znaczniki ROP
│   │   ├── sweeps.py         #   analizy parametryczne (O/F, eps, Pc...)
│   │   ├── nondimensional.py # ★ Re, Pr, Nu, Ma, Kn, St, Bi, Fo, Pe, Fr — liczone
│   │   │                     #   automatycznie z TimeHistory (walidacja reżimów)
│   │   ├── sensitivity.py    # ★ OAT, Morris, Sobol (SALib) nad api.run_batch
│   │   └── uncertainty.py    # ★ propagacja niepewności Monte Carlo:
│   │                         #   rozkłady wejść (a±, n±, Cd±, rho±, T±) →
│   │                         #   pasma Pc±, F±, Isp±, It± (percentyle 5/50/95)
│   ├── export/
│   │   ├── tables.py         #   CSV, XLSX, JSON, YAML
│   │   └── pdf_report.py     #   raport NASA-style (struktura: §10)
│   ├── validation/
│   │   └── benchmarks.py     #   automatyczne porównania: HRAP CSV (prusak_v2),
│   │                         #   CEA, literatura; raport odchyłek
│   └── gui/                  # PySide6 (ostatni etap) — klient api.py
│       ├── main_window.py    #   zakładki: Misja | Propelenty | Geometria | Symulacja
│       │                     #   | ROP | Analizy | Optymalizacja | Raport
│       ├── widgets/          #   formularze, podgląd geometrii, wykresy (mpl w Qt)
│       └── viewmodels/       #   separacja GUI ↔ core (MVVM)
├── tests/                    # pytest, lustrzana struktura pakietu
├── examples/                 # skrypty: prusak_v2, silnik 1 kN PE/N2O, EuRoC 3 km
└── docs/                     # architektura, opisy modeli, źródła równań
```

Reguła zależności: `physics/` ← wszystkie moduły fizyczne ← `simulation/` ←
`oppoints/` ← (sizing, optimization, analysis, export, gui). Import w drugą stronę
= błąd architektury (pilnowane testem importów).

## 4. Przepływ danych

```
                    ┌────────────────────────────────────────────────┐
                    │              EngineConfig (YAML/GUI)           │
                    │  misja · utleniacz · paliwo · geometria · dysza│
                    │  + version + rozkłady niepewności (opcjonalne) │
                    └───────────────┬────────────────────────────────┘
                                    ▼
                            ┌──────────────────┐
                            │     api.run      │◀── batch/ (macierz przypadków)
                            └───────┬──────────┘◀── optimization/ (mutacje configu)
   ┌──────────┐   tablice          ▼
   │ cea/     │────────────▶┌──────────────────┐
   │ +cache   │ c*,T,γ,M(of,│  simulation/     │  pętla czasowa (logika HRAP):
   └──────────┘  Pc,eps)    │  solver          │  1. zbiornik → stan utleniacza
        ▲                   └────────┬─────────┘  2. wtryskiwacz → mdot_ox
        │                            │            3. iteracja Pc: regresja(G) →
   ┌────┴─────┐                      │               mdot_f → O/F → c* → Pc
   │ tank/    │             ┌────────▼─────────┐  4. dysza → F, Isp
   │ injector/│             │   TimeHistory    │  5. geometria: w += rdot·dt
   │regression│             │  (pełne przebiegi)│ 6. eventy (LRO, burnout)
   │ geometry/│             └────────┬─────────┘
   │ nozzle/  │                      ▼
   └────┬─────┘             ┌──────────────────┐
        │ równania          │   oppoints/  ★   │  średnie ważone, punkty projektowe,
   ┌────▼─────┐             │                  │  fazy, percentyle impulsu
   │ physics/ │             └────────┬─────────┘
   └──────────┘   ┌──────────┬───────┴──────┬──────────────┬─────────────┐
                  ▼          ▼              ▼              ▼             ▼
            nozzle/     analysis/      optimization/  analysis/     export/
            sizing      nondim,        (cele nad ROP) plots,        (raport PDF
            (wybór ROP) sensitivity,                  sweeps        NASA-style)
                        uncertainty
```

Tryby pracy:

* **Analiza (forward):** `api.run(config)` → symulacja → ROP → analizy/raport.
* **Sizing (inverse):** wymagania misji → `sizing/preliminary` → wstępny config →
  symulacja → iteracyjne domknięcie na ROP.
* **Batch:** `api.run_batch(matrix)` → N przypadków równolegle → DataFrame.
* **Optymalizacja:** drivery mutują config, cele/ograniczenia liczone na ROP.
* **Wrażliwość/niepewność:** `analysis/sensitivity`, `analysis/uncertainty`
  nad `run_batch` (Monte Carlo / Sobol / Morris / OAT).

## 5. Kluczowe interfejsy (sygnatury poglądowe)

```python
# api.py — publiczne API (GUI i CLI to tylko klienci)
def run(config: EngineConfig) -> SimulationResult: ...
def run_batch(cases: CaseMatrix, n_jobs: int = -1) -> pd.DataFrame: ...
def size(mission: MissionRequirements) -> EngineConfig: ...


class ThermochemistryBackend(ABC):
    def query(self, of: float, pc: float, eps: float) -> CEAResult: ...


@register_model("regression")  # rejestr pluginów (core/registry.py)
class PowerLawRegression(RegressionModel):
    def rdot(self, g_flux: float, state: PortState) -> float: ...  # [m/s]


class GrainGeometry(ABC):
    # w = grubość spalona [m]; wszystko jako funkcja w → dowolny kształt portu
    def port_area(self, w) -> float: ...
    def burn_perimeter(self, w) -> float: ...
    def hydraulic_diameter(self, w) -> float: ...
    def fuel_volume(self, w) -> float: ...
    def web_remaining(self, w) -> float: ...


class TankModel(ABC):
    def step(self, dt: float, mdot_out: float) -> TankState: ...


class InjectorModel(ABC):
    def mdot(self, upstream: FluidState, p_chamber: float) -> float: ...
```

## 6. Stos technologiczny

NumPy · SciPy · Pandas · Matplotlib · Pint · RocketCEA · Cantera (fallback) ·
CoolProp (właściwości utleniaczy) · pymoo (NSGA-II) · **SALib (Sobol/Morris)** ·
pydantic (config + wersjonowanie) · PyYAML · openpyxl (XLSX) ·
reportlab lub szablon LaTeX (PDF — decyzja D8) · PySide6 · pytest ·
multiprocessing (batch).

## 7. Plan etapów

| Etap | Zakres | Walidacja |
|---|---|---|
| E1 | `core/` (units, constants, config+version, registry, logging, exceptions) + `data/` + szkielet `api.py` | testy jednostkowe, spójność z 01_Sizing.xlsx |
| E2 | `physics/` (compressible, gas_dynamics, thermodynamics — zakres potrzebny E3–E6) + `cea/` | krzyż RocketCEA↔Cantera↔07_cantera_*.py; Sutton przykłady liczbowe |
| E3 | `geometry/`: cylindryczny → multiport → star/wagon/custom | analityczne przypadki testowe |
| E4 | `regression/` + `nozzle/` + `performance/` | dane a,n z literatury; Sutton |
| E5 | `tank/` (equilibrium blowdown N2O) + `injector/` (SPI/NHNE/HEM) | ESDU 91022, Twój 08_injector, HRAP theory |
| E6 | `simulation/solver` + pełne `api.run` | **benchmark vs prusakv2_HRAP_output.csv** |
| E7 | `oppoints/` ★ | testy na przebiegach z E6 |
| E8 | `sizing/` + `chamber/` + `nozzle/sizing` | porównanie z Twoim sizingiem 1 kN (ε 5.2–5.3) |
| E9 | `batch/` + `analysis/` (plots, sweeps, **nondimensional, sensitivity, uncertainty**) | przypadki testowe SALib; sanity-check liczb bezwymiarowych |
| E10 | `export/` (tabele + **raport NASA-style**) + `database/` | przegląd raportu |
| E11 | `optimization/` (scipy → NSGA-II) | odtworzenie 09_optymalizacja_OF |
| E12 | `gui/` PySide6 + dokumentacja końcowa, przykłady, pakiet | testy manualne + pełny regres |

Po każdym etapie: opis algorytmu + równania + źródła → kod → testy → **Twoje uwagi**.

## 8. Punkty decyzyjne modeli fizycznych (do rozstrzygnięcia w odpowiednich etapach)

| # | Decyzja | Opcje (zalety/wady w opisie etapu) | Etap |
|---|---|---|---|
| D1 | Właściwości N2O | **ROZSTRZYGNIĘTE (2026-07-16): obie z przełącznikiem — ESDU w pętli solvera, CoolProp dla HEM/NHNE i walidacji** | E5 ✓ |
| D2 | Model zbiornika N2O | **ROZSTRZYGNIĘTE (2026-07-16): równowagowy adiabatyczny (HRAP); Z–K jako przyszłe rozszerzenie za interfejsem TankModel** | E5 ✓ |
| D3 | Wtryskiwacz dwufazowy | **ROZSTRZYGNIĘTE (2026-07-16): SPI domyślny (zgodność z HRAP i kalibracjami Cd); NHNE i HEM zaimplementowane jako opcje** | E5 ✓ |
| D4 | Strumień masowy w regresji | **ROZSTRZYGNIĘTE (2026-07-16): G_ox domyślnie (spójne z bazą HRAP); G_total dostępne przełącznikiem flux_basis** | E4 ✓ |
| D5 | Solver Pc w kroku czasowym | iteracja punktu stałego (HRAP, masz w 06) vs Brent na bilansie masy (pewniejsza zbieżność) | E6 |
| D6 | Przepływ w dyszy (CEA) | **ROZSTRZYGNIĘTE (2026-07-16): shifting equilibrium domyślnie; frozen zawsze liczone obok jako dolna granica; Bray opcjonalnie później** | E2 ✓ |
| D7 | Faza gazowa blowdown | politropa par N2O (HRAP) vs real-gas CoolProp | E5 |
| D8 | Raport PDF | reportlab (czysty Python) vs szablon LaTeX (spójny z Twoimi .tex) | E10 |
| D9 | Metody wrażliwości — domyślna | Morris (tani screening) vs Sobol (pełne indeksy, drogi) vs OAT (najprostszy) | E9 |
| D10 | Format `database/` | pliki YAML/JSON w katalogach (git-friendly) vs SQLite (zapytania, integralność) | E10 |

## 9. Strategia walidacji

1. **CEA:** każdy backend porównany z opublikowanymi wynikami CEA (RP-1311) oraz
   krzyżowo RocketCEA↔Cantera (tolerancje: c* < 0.5%, Tc < 1%).
2. **HRAP:** E6 odtwarza `prusak_v2` i porównuje przebiegi F(t), Pc(t), O/F(t),
   m(t) z `prusakv2_HRAP_output.csv`; raport odchyłek RMS/max.
3. **Literatura:** regresja (Karabeyoglu — parafina; Chiaverini — HTPB; PE z Twoich
   źródeł), dysza (Sutton przykłady liczbowe), N2O (ESDU/CoolProp vs tablice).
4. **Twoje dane:** spójność z 01_Sizing.xlsx i solverem 06 (świadomie konserwatywne
   założenia będą udokumentowane jako różnice, nie błędy).
5. **Reżimy fizyczne:** `analysis/nondimensional` automatycznie flaguje wyjście poza
   zakres ważności modeli (np. Re poza korelacją, Ma > 0.3 w porcie).

## 10. Raport końcowy (NASA-style)

Generowany automatycznie dokument o strukturze publikacji technicznej:

1. Mission Requirements · 2. Inputs & Assumptions · 3. Propellants
4. Thermochemistry (CEA) · 5. Grain & Chamber Geometry · 6. Transient Simulation
7. Representative Operating Points (porównanie średnich: czasowa vs ważona impulsem;
   udziały faz w It; % czasu → 90/95/99% It; rekomendacje punktów: dysza / analiza
   cieplna / wytrzymałość — z uzasadnieniem) · 8. Nozzle Design · 9. Performance
10. Sensitivity & Uncertainty (tornado, pasma ±) · 11. Optimization
12. Validation · 13. Conclusions · Załączniki: config YAML, log solvera, tabele.
