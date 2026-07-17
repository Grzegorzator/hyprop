"""Material-card dialogs for user-defined propellants (GUI 'custom...').

Fuel card: fully solver-compatible (composition + hf -> Cantera
surrogate; own regression coefficients). Oxidizer card: user picks the
chemistry base species (N2O / O2 / H2O2 - GRI-Mech limits); the
equilibrium blowdown tank stays N2O-only, so pressure_fed is advised.
All values are marked verify=True in the saved YAML.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QMessageBox,
)

from hyprop.data.custom import (
    OXIDIZER_BASE_SPECIES,
    save_custom_fuel,
    save_custom_oxidizer,
)


class _CardDialog(QDialog):
    """Base: form of labelled QLineEdits + OK/Cancel."""

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.form = QFormLayout(self)
        self.edits: dict = {}

    def add_field(self, key: str, label: str, default: str = "") -> None:
        edit = QLineEdit(default)
        self.form.addRow(label, edit)
        self.edits[key] = edit

    def add_buttons(self) -> None:
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.form.addRow(buttons)

    def value(self, key: str, cast=float, default=None):
        text = self.edits[key].text().strip()
        if not text:
            return default
        return cast(text)


class FuelCardDialog(_CardDialog):
    """Collects a custom fuel definition; returns the saved name."""

    def __init__(self, parent=None) -> None:
        super().__init__("Custom fuel - material card", parent)
        self.form.addRow(QLabel(
            "SI units. Composition per formula unit; hf per that unit.\n"
            "Values are stored with verify=True (confirm by fire tests)."))
        self.add_field("name", "Name (identifier)")
        self.add_field("rho", "Density [kg/m3]")
        for element in ("C", "H", "O", "N"):
            self.add_field(element, f"Atoms of {element} [-]",
                           "0" if element in ("O", "N") else "")
        self.add_field("hf", "Enthalpy of formation [J/mol]")
        self.add_field("a", "Regression a [m/s/(kg/m2/s)^n] (optional)")
        self.add_field("n", "Regression n [-] (optional)")
        self.add_buttons()

    def save(self) -> str:
        name = self.edits["name"].text().strip()
        composition = {el: self.value(el, float, 0.0) or 0.0
                       for el in ("C", "H", "O", "N")}
        path = save_custom_fuel(
            name=name,
            density_kg_m3=self.value("rho"),
            composition=composition,
            hf_j_mol=self.value("hf"),
            regression_a_si=self.value("a", float, None),
            regression_n=self.value("n", float, None),
        )
        return path.stem


class OxidizerCardDialog(_CardDialog):
    """Collects a custom oxidizer definition; returns the saved name."""

    def __init__(self, parent=None) -> None:
        super().__init__("Custom oxidizer - material card", parent)
        self.form.addRow(QLabel(
            "Chemistry base = species used in combustion equilibrium\n"
            "(GRI-Mech limit). Blowdown tank model stays N2O-only;\n"
            "use tank model 'pressure_fed' for other oxidizers."))
        self.add_field("name", "Name (identifier)")
        self.base = QComboBox()
        self.base.addItems(list(OXIDIZER_BASE_SPECIES))
        self.form.addRow("Chemistry base", self.base)
        self.add_field("molar", "Molar mass [kg/mol]")
        self.add_field("rho", "Reference density [kg/m3] (optional)")
        self.add_buttons()

    def save(self) -> str:
        path = save_custom_oxidizer(
            name=self.edits["name"].text().strip(),
            base=self.base.currentText(),
            molar_mass_kg_mol=self.value("molar"),
            reference_density=self.value("rho", float, None),
        )
        return path.stem


def open_material_card(kind: str, parent=None):
    """Run the dialog; returns the new database name or None."""
    dialog = (FuelCardDialog(parent) if kind == "fuel"
              else OxidizerCardDialog(parent))
    while dialog.exec() == QDialog.Accepted:
        try:
            return dialog.save()
        except Exception as exc:                       # noqa: BLE001
            QMessageBox.warning(parent, "Invalid card", str(exc))
    return None
