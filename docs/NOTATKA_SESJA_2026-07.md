# HyProp — notatka podsumowująca sesję (15–17.07.2026)

Współautorzy: MASSLACZEK12 (decyzje projektowe, modele fizyczne) + Claude
(implementacja). Repozytorium: https://github.com/Grzegorzator/hyprop

## Co powstało

Kompletne środowisko inżynierskie do preliminary sizing hybrydowych silników
rakietowych — od wymagań misji, przez symulację czasową w logice HRAP i moduł
reprezentatywnych punktów pracy (ROP), po optymalizację, raporty NASA-style
i GUI. Wszystkie 12 zaplanowanych etapów (E0–E12) ukończone; **125 testów
pytest przechodzi**; wersja 0.1.0.

## Przebieg etapów

| Etap | Zakres | Kluczowy wynik |
|---|---|---|
| E0 | Architektura v0.2 (`docs/ARCHITECTURE.md`) | 16 modułów za interfejsami ABC; po recenzji współautora (9.8/10) dodano warstwę `physics/`, API-first, rejestr pluginów, analizy wrażliwości/niepewności, batch, database, raport NASA-style |
| E1 | `core/` + `data/` | Pint (config przyjmuje "35 bar"), EngineConfig (pydantic, wersjonowany), rejestr `@register_model`, bazy YAML 5 paliw / 4 utleniaczy ze źródłami i flagami `verify` |
| E2 | `physics/compressible` + `cea/` | Backend Cantera (uogólnienie skryptu 07 użytkownika) zwalidowany: Tc 3292 K, γ 1.247, Isp 247 s @ parafina/N2O O/F 6.5 — zgodność <1%; RocketCEA gotowy (wymaga MinGW) |
| E3 | `geometry/` | 5 geometrii ziarna jako f(w); star/wagon/custom przez wspólny silnik offsetu konturu (shapely) |
| E4 | `regression/` + `nozzle/losses` + `performance/` | r˙=a·Gⁿ·Lᵐ; konwencja jednostek HRAP potwierdzona w `propellant_template.m` (r˙ mm/s, G kg/m²s) |
| E5 | `tank/` + `injector/` | ESDU 91022 (przeniesione 1:1 z solvera 06) + CoolProp, walidacja krzyżowa <1.5%; zbiornik równowagowy HRAP; wtryskiwacze SPI/HEM/NHNE |
| E6 | solver czasowy + benchmark | Pętla HRAP z tablicami CEA; **benchmark vs prusak_v2: Pc 1.7%, P_tank 0.6%, O/F 1.0%, F 6.2%** (nadwyżka F = różnica metodyczna equilibrium-ve vs tablice RPA) |
| E7 | `oppoints/` (ROP) | Średnie ważone (domyślnie ciągiem), punkty peak/impulse-weighted/heat-load/mass-flow/median, percentyle It, fazy; demo: średnia czasowa zaniża F o 51.5% |
| E8 | `api.size` + ISA + dysza/komora na ROP | Sizing odwrotny z pętlą dostrajającą; adaptacja ε na wysokości projektowej |
| E9 | `batch/` + `analysis/` | Grid/LHS, wrażliwość OAT/Morris/Sobol, Monte Carlo (pasma p5/50/95), liczby Re/Ma z flagami reżimów |
| E10 | `export/` + `database/` | CSV/XLSX/JSON, raport LaTeX→PDF (rozdział ROP z rekomendacjami), baza YAML silników/materiałów/wtryskiwaczy/testów |
| E11 | `optimization/` | Differential evolution (scipy) + NSGA-II (pymoo); cele/ograniczenia na metrykach ROP |
| E12 | `gui/` PySide6 | MVVM (viewmodel bez Qt, testowalny); zakładki, run w wątku, wykresy z markerem LRO |

## Rozstrzygnięte decyzje modeli fizycznych (D1–D10)

D1 właściwości N2O: **ESDU 91022 + CoolProp** z przełącznikiem · D2 zbiornik:
**równowagowy adiabatyczny (HRAP)** · D3 wtryskiwacz: **SPI domyślny** (NHNE/HEM
opcjonalnie) · D4 strumień regresji: **G_ox** (spójny z bazą HRAP; G_total
przełącznikiem) · D5 solver Pc: **fixed-point** (≡ Brent w 1–2%) · D6 dysza:
**shifting equilibrium** domyślnie, frozen raportowane jako dolna granica ·
D7 faza gazowa: politropa k=1.27 (real-gas — otwarte) · D8 raport: **LaTeX** ·
D9 wrażliwość: **OAT** jako screening · D10 baza: **YAML w katalogach**.

## Zaprojektowany silnik: HDPE/N2O 0.5 kN, misja 0 → 3000 m

`examples/hdpe_05kN_3km_sized.yaml` (api.size, 5 iteracji): F_iw = 494 N,
It = 4083 N·s, Pc_iw = 32 bar, Isp_iw = 221 s, LRO 7.24 s. Ziarno port ⌀26 →
OD ⌀43.1 × 508 mm; zbiornik 2.40 L / 1.66 kg N2O; wtrysk 4×⌀1.65 mm Cd 0.6;
gardziel ⌀11.7 mm, ε = 5.02 adaptowane na 1000 m (bez ryzyka separacji na 0 m).
Trajektoria 1-DOF (m_dry = 7.0 kg bottom-up, D = 0.10 m, Cd = 0.55): apogeum
**3832 m** (+28% zapasu; stały Cd zaniża opór transoniczny przy Ma 0.88),
wypalenie na 2354 m, TWR₀ 6.8. Raport: `examples/export_demo/report_hdpe_05kN_3km.pdf`.

## Ważne ustalenia techniczne z sesji

* CSV HRAP `prusakv2` pochodzi ze starszej konfiguracji niż `.mat` —
  wejścia zrekonstruowano z samego CSV; implikowane a = 1.040e-4 SI
  niezależnie potwierdziło konwersję jednostek.
* Błąd złapany w E6: zbyt duże cp molowe surogatu paliwa więziło równowagę
  Cantery w zimnym rozwiązaniu (HDPE: Tc 1119 K zamiast 3339 K) — cp skalowane
  masą molową; po poprawce c\*max HDPE przy O/F 8.2 = dokładnie `opt_OF` HRAP.
* Sprzężenie blowdown bywa nieintuicyjne: wzrost η_c\* podnosi Pc, dławi
  wtryskiwacz i **obniża** ciąg (wrażliwość −0.61%/1%).
* Temperatury zbiornika nie wolno perturbować względnie (±5% z 293 K sięga
  punktu krytycznego N2O) — w MC deklarować rozkładem w kelwinach.
* NumPy 2.x usunął `np.trapz` → shim `_trapz` (trapezoid) w całym kodzie.

## GUI (przetestowane przez użytkownika na Windows / Python 3.14)

Pasek menu File | Options → **Units** (SI / Metric mm-L-bar-°C / Imperial
in-psi-lbf-°F; config wewnętrznie zawsze SI, konwersja Pint tylko na widoku),
listy rozwijane dla pól wyboru (paliwo, utleniacz, geometria, wtryskiwacz,
zbiornik, solver Pc — zasilane z bazy i rejestru pluginów), pozycja
**"custom..."** otwierająca kartę materiałową (paliwo: skład+hf+a,n — w pełni
liczone przez solver; utleniacz: gatunek bazowy n2o/gox/htp, zbiornik blowdown
pozostaje N2O-only), Results z wykresami i markerem LRO, eksport i raport
z poziomu okna.

## Dystrybucja

`git clone` → `install_windows.bat` (tworzy `.venv`, instaluje wszystko,
selftest) → `run_gui.bat`. Na czystym Windowsie ręcznie tylko: **Python
3.11–3.14** (z "Add to PATH") i **Git**; opcjonalnie MiKTeX (PDF) i
RocketCEA+MinGW. Karty materiałowe w `database/` commitują się — wspólna baza
zespołu. Commity/push wykonuje użytkownik przez `commit.bat`.

## Roadmapa (po v0.1)

Kalibracja a, n, Cd, η_c\* z danych hamowni (`database/tests/`) — sugerowany
następny krok przed EuRoC; zbiornik nierównowagowy Zilliac–Karabeyoglu; Bray
(frozen od gardzieli); real-gas faza gazowa (D7); erozja dyszy; moduł
trajektorii sprzężony z sizingiem (zamiast heurystyki h=apogeum/3); walidacja
RocketCEA na Windows; OpenMDAO; CFD.
