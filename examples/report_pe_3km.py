"""E10 demo: full export + NASA-style report for the 0.5 kN engine."""
import sys; sys.path.insert(0, '.')
import hyprop.simulation.solver as sm
sm._TABLE_OF, sm._TABLE_PC = 6, 5
import hyprop.api as api
from hyprop.export import export_result, generate_report
from hyprop.oppoints import analyze

config = api.load_config("examples/pe_05kN_3km_sized.yaml")
result = api.run(config)
rop = analyze(result)

files = export_result(result, "outputs/pe_05kN_3km", config=config,
                      rop=rop, stem="pe_05kN_3km")
report = generate_report(config, result, rop,
                         "outputs/pe_05kN_3km/report_pe_05kN_3km")
print("Exported:", *(f.name for f in files))
print("Report  :", report)
