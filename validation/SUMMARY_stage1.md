## Podsumowanie etapu 1

### Zwalidowane (niezależna referencja, PASS)

* **Termochemia PE/N2O** (pkt 2): siatka O/F 3–10 × Pc 10–50 bar, równowaga i zamrożenie, wobec oficjalnego pakietu NASA `cea` przy tym samym ΔHf. Wielkości: Tc, M, γ_s, γ, c*, Isp i T wylotu.
  * RocketCEA: ≤ 0.28 % w całej siatce.
  * Cantera: ≤ 0.33 % dla C/O < 1 (O/F > ~3.2). Przy O/F 3 brakuje jej węgla stałego, błąd do 1.4 % w Tc i 3.9 % w T wylotu; backend ostrzega.
* **Przepływ w dyszy** (pkt 3): relacje izentropowe, C_F i praca poza punktem projektowym. Przykłady 3-1 do 3-4 i 3-7 z Suttona: 12/12.
* **Własności N2O** (pkt 4): p_sat, ρ_l i ρ_v z ESDU 91022 w granicach 2 % od EOS Lemmon & Span w zakresie 183–297 K. Stałe krytyczne zgodne.
* **Analiza wymiarowa** (pkt 9): 10/10 relacji rdzenia zgodnych z Pintem do 1e-14. Pint występuje tylko na granicy konfiguracji (`to_si`).
* **Niezmienniki** (pkt 7, Hypothesis):
  * bilans masy utleniacza i paliwa;
  * impuls = ∫F dt;
  * port rośnie monotonicznie;
  * Pc mieści się między ciśnieniem otoczenia a ciśnieniem w zbiorniku;
  * wynik nie zależy od jednostek wejścia.
* **Zbieżność** (pkt 8): rząd 1 w dt (jawny Euler, zgodnie z oczekiwaniem). Przy dt = 0.01 s błąd It wynosi 0.015 %, Pc fazy ciekłej 0.009 %, LRO 1 krok. Tolerancja solvera Pc 1e-4 wpływa na It poniżej 0.002 %.

### Częściowo zwalidowane

* **Wtryskiwacz** (pkt 5): jedyny punkt literaturowy możliwy do odczytania ze źródła to Waxman i in. (NTRS 20190001326): Cd_eff ≈ 0.6 przy ΔP = 2.28 MPa i T1 = 280 K.
  * HEM daje 0.57–0.59, NHNE 0.69–0.70.
  * SPI (domyślny, jak w HRAP) z Cd dopasowanym w zakresie jednofazowym daje 0.77. Przeszacowuje więc ṁ w zakresie dwufazowym o ~28 %.
  * prusak_v2 pracuje przy ΔP ≈ 1.7 MPa, blisko przejścia. Cd i model wtryskiwacza wymagają próby na zimno (cold flow).
* **Zbiornik**: tylko porównanie kod–kod (HRAP; ESDU vs CoolProp zmienia It o 0.04 %). Danych pomiarowych blowdown (Whitmore & Chandler, Zimmerman) nie ma w folderze literatury.
* **ESDU h_lv i cp_l**: h_lv (skalowanie Watsona) odbiega o +1.6 do +2.8 % w zakresie 280–305 K, cp_l o 3.3 % przy 198 K i silnie powyżej 297 K. Wpływ na It wynosi 0.04 %. Powyżej 297 K kod loguje ostrzeżenie.
* **Benchmark HRAP**: porównanie kod–kod, zgodność ciągu częściowo przypadkowa (opis w sekcji 2.5).

### Niemożliwe do zwalidowania bez nowych danych

* **Regresja PE/N2O (a, n)**: preset HRAP (0.104 mm/s, n 0.352) o nieudokumentowanym pochodzeniu. Teraz porównany z literaturą (pkt 6):
  * Kamps i in. 2019 (N2O/HDPE, G_ox 50–100 kg/m²s): ṙ = 2.52e-5·G^0.76 (history) lub 4.36e-5·G^0.62 (endpoint), w m/s. Preset jest wolniejszy o 16–37 % w tym zakresie. Przy G_ox ≈ 260 kg/m²s (start prusak_v2, ekstrapolacja) jest wolniejszy 1.9–2.3 raza.
  * Doran 2007 podaje n = 0.331 (za Kampsem), blisko presetu.
  * Wpływ na przykład 0.5 kN: z prawem Kampsa O/F_iw spada z 6.1 do 3.1–3.6 (silnik bogaty w paliwo, blisko obszaru C/O ≈ 1, gdzie trzeba użyć RocketCEA), a It o 2.5–3 %.
  * **Wniosek**: n między 0.33 a 0.76 to największa niepewność sizingu. Bez pomiaru a i n dla Waszego PE w kilku punktach G_ox wynik sizingu jest tylko orientacyjny.
* **η_c***: domyślne 0.95 jest powyżej zakresu zmierzonego przez Kampsa dla N2O/HDPE (87–94 %).
* **Cd wtryskiwacza, gęstość LDPE i jego krystaliczność** (wpływa na ΔHf, ok. 3 K w Tc): wymagają prób lub pomiarów.
* **NIST WebBook**: tabeli nie udało się pobrać. Plik CSV wrzucony do `validation/data/nist_n2o_sat.csv` zostanie użyty automatycznie.

### Błędy znalezione i poprawione w pkt 2–9 (osobne commity `fix(...)`)

* `fix(cea)`: Cantera poza zakresem ważności (C/O ≥ 1), dodane ostrzeżenie i funkcja `carbon_to_oxygen_ratio`.
* `fix(tank)`: w kroku wyczerpania cieczy (LRO) znikała masa utleniacza (do jednego kroku przepływu).
* `fix(config)`: wartości z jednostkami w `grain.port` (np. "28 mm") wywracały geometrię.
* `fix(performance)`: współczynnik dywergencji λ tylko na członie pędowym (Sutton, równ. 3-34).
* N2O: ostrzeżenie dla ESDU powyżej 297 K.
* Obserwacja: preset HRAP „Paraffin” [0.0304, 0.681] to współczynniki HTPB/LOX z tabeli 1.1 u Waxmana.

