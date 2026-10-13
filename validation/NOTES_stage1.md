## 2. Ustalenia (etap 1, pkt 0–1)

### 2.1 Testy

* Python 3.11, wszystkie backendy (Cantera 3.2, CoolProp 8.0, RocketCEA 1.2.3 zbudowany z gfortran, pymoo 0.6, openpyxl): **126 passed, 0 skipped, 0 failed**.
* 3 skipy z czystej instalacji to **nie** RocketCEA/Cantera/pymoo, tylko: 2× `importorskip("CoolProp")` w `test_tank_injector.py` oraz cały moduł `test_cea.py` (`importorskip("cantera")` na poziomie modułu – 8 testów liczonych jako 1 skip). Stąd 119 vs 126.
* **RocketCEA, NSGA-II (pymoo) i Morris/Sobol (SALib) nie mają żadnego testu.** Ich instalacja nie zmienia wyniku pytest – nigdy nie są wywoływane.
* Ostrzeżenie shapely `resolution` → `quad_segs`: potwierdzone (16×), do etapu 3.

### 2.2 Błędy w kodzie (do osobnych commitów `fix(...)`, po akceptacji)

| ID | Problem | Skutek | Proponowana poprawka |
|---|---|---|---|
| B1 | `_build_cea_table`: klucz cache `round(eps, 2)`, a `TabulatedBackend.query` wymaga \|Δeps\| < 1e-9 | `examples/size_hdpe_3km.py` (= `api.size`) pada z `ValueError`. Z poprawionym kluczem wyniki z README odtwarzają się co do cyfry (wiersze 24–27). | Klucz na pełnej wartości `float(eps)`. Bez zmiany fizyki. |
| B2 | `simulation.cea_backend` jest ignorowany; solver ma na sztywno `CanteraBackend` | Symulacja i sizing **zawsze** liczą Cantera, wbrew README („RocketCEA primary”) i wbrew konfiguracji. Wszystkie liczby transient w README są z Cantery. | Honorować `cea_backend` przez `get_backend()`. Uwaga: zmieni liczby przy `auto` + RocketCEA, patrz B3 – wymaga decyzji. |
| B3 | `StationState.gamma` znaczy co innego w backendach: Cantera = cp/cv zamrożone (1.247), RocketCEA = γ_s równowagowe (1.167) | `chamber.gamma` trafia do historii i do doboru dyszy (`nozzle/sizing.py`: eps_opt, Cf). Po naprawie B2 wynik sizingu zależałby od backendu o ~7 % w γ. | Dwa jawne pola: `gamma_frozen` i `gamma_eq`; sizing dyszy świadomie wybiera jedno. Wpływ na eps/Cf policzę w pkt 2–3. |
| B4 | η_c* nie wchodzi do ciągu: `F = η_noz·ṁ·v_e,ideal + (p_e − p_a)·A_e`, gdzie v_e i p_e są idealne (CEA) | η_c* obniża tylko Pc. Isp dostarczony = η_noz·Isp_ideal niezależnie od η_c*. `sensitivity_hdpe.py` pokazuje ∂F_iw/∂η_c* = −0.61 (lepsze spalanie → mniejszy ciąg). Przy η_c* = 0.95 ciąg i Isp zawyżone o ~5 % względem konwencji Isp_del = η_c*·η_F·Isp_ideal. | **Decyzja fizyczna – do omówienia.** HRAP ma tę samą konstrukcję (Nickel, „Theory and Application of HRAP”, r. V, równ. 20–22: v_e z idealnego T_c), więc benchmark z HRAP tego nie wykrywa. Źródło konwencji η_c*·η_F podam z numerem równania w pkt 3 – nie cytuję z pamięci. |

### 2.3 Niezgodności dokumentacji

* **D1** README: „LRO 7.19 s vs ~7.5 s” (HRAP). Z CSV HRAP: ṁ_ox spada 0.317 → 0.114 kg/s przy **t = 6.955 s**. HyProp jest więc o 3.4 % *później*, a nie wcześniej.
* **D2** Apogeum 3291 m dotyczy m_dry = 9 kg. Commit `d22b828` zmienił skrypt na 7 kg → obecnie 3832 m. README nieaktualne.
* **D3** γ = 1.245 w README; skrypt 07 i HyProp dają 1.247.
* **D4** Liczba testów: README podaje 120 i 125, faktycznie 126.
* **D5** „Cantera fallback validated to <1 %”: prawda dla Tc, c*, Isp (≤ 0.15 % vs NASA CEA), nieprawda dla γ (B3), a w transient RocketCEA nigdy nie jest używany (B2).
* **D6** Higiena przykładów (do etapu 3): `benchmark_prusak_v2.py` ma na sztywno ścieżkę `/sessions/festive-nice-darwin/...`; `report_hdpe_3km.py` nie znajduje figury (`../../examples/...`); przykłady nadpisują śledzone pliki (`database/engines/sized_hdpe_500N.yaml`, PNG w `examples/`).
* **D7** (HRAP, informacyjnie) kolumna CSV „Regression Rate (mm/s)” zawiera wartości w m/s. Potwierdza to przyrost średnicy portu.

### 2.4 Wyjaśnienie różnicy ~2.3 % c*

Skrypt 07 liczy c* wzorem gazu idealnego z γ = cp/cv mieszaniny **zamrożonej** w komorze. HyProp/CEA podaje c* **równowagowe** (zmiana składu w zbieżnej części dyszy). Ten sam wzór z równowagowym γ_s z NASA CEA odtwarza c* CEA z dokładnością 0.13 % (wiersz 43). Całe 2.3 % wynika więc z definicji γ, a nie z różnicy w termochemii.

### 2.5 Co te zgodności faktycznie dowodzą

* Benchmark HRAP to porównanie **kod–kod**: ten sam model zbiornika, ten sam SPI i te same współczynniki. Zgodność dowodzi wierności implementacji HRAP, a nie poprawności fizycznej (patrz B4).
* Kotwica „07” to Cantera vs Cantera (gri30, to samo Hf), czyli test spójności.
* Na razie naprawdę niezależne są dwie referencje: NASA CEA (przez RocketCEA) i CoolProp (EOS Lemmon & Span 2006). Obie dostają jednak te same dane wejściowe HyProp, np. Hf paliwa.
* Hf parafiny C32H66 = −703 kJ/mol to oszacowanie **fazy gazowej** z addytywności grupowej. W silniku paliwo jest stałe, więc entalpia przemiany fazowej jest pominięta. Wpływ na Tc/c* wymaga referencji NIST w pkt 2; nie podaję liczby bez źródła.
* HTPB nie ma Hf w bazie, więc żaden backend nie policzy HTPB/N2O. Siatka z pkt 2 wymaga składu i Hf HTPB ze źródłem.
* Luka ciągu 6.2 % vs HRAP: ok. 2.9 pp wyjaśnia wylot równowagowy vs zamrożony (wiersz 8). Pozostałe ~3.3 pp są na razie niewyjaśnione (kandydaci: η_noz stosowane tylko do członu pędowego w HyProp vs całego ciągu w HRAP, γ_e = const w HRAP, dynamika napełniania komory w HRAP). Do pkt 5.
