"""Physical constants used throughout HyProp.

All values are in SI base units. Every constant carries its source.
No other module may hard-code these values (no magic numbers rule).
"""

#: Standard gravitational acceleration [m/s^2].
#: Source: ISO 80000-3:2019; also NIST CODATA (exact, by definition).
G0: float = 9.80665

#: Universal gas constant [J/(mol*K)].
#: Source: CODATA 2018 (exact, by SI redefinition of 2019).
R_UNIVERSAL: float = 8.314462618

#: Sea-level standard atmospheric pressure [Pa].
#: Source: ISO 2533:1975 (International Standard Atmosphere).
P_ATM_SL: float = 101_325.0

#: Sea-level standard temperature [K].
#: Source: ISO 2533:1975 (International Standard Atmosphere).
T_ATM_SL: float = 288.15

#: Standard reference temperature for thermochemistry [K].
#: Source: NASA RP-1311 (CEA) reference state, 298.15 K.
T_REF_THERMO: float = 298.15
