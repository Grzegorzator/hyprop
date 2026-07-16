"""1-DOF vertical trajectory check for the sized 0.5 kN HDPE engine.

Rocket assumptions (TO BE CONFIRMED by the user; scaled from the user's
06_hybrid_solver 1 kN design): m_dry = 9.0 kg (structure + avionics +
payload + dry engine + tank), D_ref = 0.10 m, Cd = 0.55 (constant).
Drag: D = 0.5 * rho_ISA(h) * v^2 * Cd * A_ref. Thrust/mdot from the
transient simulation of examples/hdpe_05kN_3km_sized.yaml.
"""
import sys; sys.path.insert(0, '.')
import numpy as np
import hyprop.simulation.solver as sm
sm._TABLE_OF, sm._TABLE_PC = 6, 5
import hyprop.api as api
from hyprop.core.constants import G0
from hyprop.physics import atmosphere

M_DRY, D_REF, CD = 9.0, 0.10, 0.55
A_REF = np.pi * (D_REF / 2) ** 2

result = api.run(api.load_config("examples/hdpe_05kN_3km_sized.yaml"))
h = result.history
t_burn, F_t = h["t"], h["thrust"]
m_prop_t = h["m_ox"] + h["m_fuel"]        # remaining propellant mass

def thrust(t):  return np.interp(t, t_burn, F_t, right=0.0)
def m_prop(t):  return np.interp(t, t_burn, m_prop_t, right=m_prop_t[-1])

dt, t, v, alt = 0.01, 0.0, 0.0, 0.0
apogee, v_max, t_burnout = 0.0, 0.0, t_burn[-1]
while v >= 0.0 or t < t_burnout:
    m = M_DRY + m_prop(t)
    drag = 0.5 * atmosphere.density(min(max(alt, 0), 19_999)) * v * abs(v) * CD * A_REF
    a = (thrust(t) - drag - m * G0) / m
    v += a * dt; alt += v * dt; t += dt
    v_max = max(v_max, v); apogee = max(apogee, alt)
    if t > 120: break

m0 = M_DRY + m_prop(0.0)
print(f"m_wet={m0:.2f} kg, TWR0={F_t[:50].max()/(m0*G0):.2f}")
print(f"v_max={v_max:.0f} m/s (Ma~{v_max/340:.2f}), burnout h={np.interp(t_burnout,[0,t],[0,alt]):.0f} m")
print(f"APOGEE = {apogee:.0f} m @ t={t:.1f} s  (target 3000 m)")
