import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PoliticaSeguridadValidator:
    """
    Lee PoliticaSeguridad.objects.first() en cada validación, así los cambios en la UI surten efecto de inmediato.
    """

    # Defaults seguros si la tabla está vacía
    DEFAULT_LONGITUD   = 8
    DEFAULT_NUMEROS    = True
    DEFAULT_MAYUSCULAS = True
    DEFAULT_SIMBOLOS   = True

    PATRON_SIMBOLOS   = r'[!@#$%^&*()\-_=+\[\]{}|;:\'",.<>?/\\`~]'
    PATRON_NUMEROS    = r'\d'
    PATRON_MAYUSCULAS = r'[A-Z]'
    PATRON_MINUSCULAS = r'[a-z]'

    def _politica(self):
        try:
            from .models import PoliticaSeguridad
            return PoliticaSeguridad.objects.first()
        except Exception:
            return None

    def validate(self, password: str, user=None) -> None:
        p       = self._politica()
        errores = []

        longitud   = p.longitud_minima     if p else self.DEFAULT_LONGITUD
        numeros    = p.requiere_numeros    if p else self.DEFAULT_NUMEROS
        mayusculas = p.requiere_mayusculas if p else self.DEFAULT_MAYUSCULAS
        simbolos   = p.requiere_simbolos   if p else self.DEFAULT_SIMBOLOS

        if len(password) < longitud:
            errores.append(ValidationError(
                _("Mínimo %(n)d caracteres."),
                code="password_too_short", params={"n": longitud}
            ))
        if not re.search(self.PATRON_MINUSCULAS, password):
            errores.append(ValidationError(
                _("Debe contener al menos una letra minúscula."),
                code="password_no_lower"
            ))
        if mayusculas and not re.search(self.PATRON_MAYUSCULAS, password):
            errores.append(ValidationError(
                _("Debe contener al menos una letra mayúscula."),
                code="password_no_upper"
            ))
        if numeros and not re.search(self.PATRON_NUMEROS, password):
            errores.append(ValidationError(
                _("Debe contener al menos un número."),
                code="password_no_digit"
            ))
        if simbolos and not re.search(self.PATRON_SIMBOLOS, password):
            errores.append(ValidationError(
                _("Debe contener al menos un carácter especial (!@#$%...)."),
                code="password_no_symbol"
            ))

        if errores:
            raise ValidationError(errores)

    def get_help_text(self) -> str:
        p          = self._politica()
        longitud   = p.longitud_minima     if p else self.DEFAULT_LONGITUD
        numeros    = p.requiere_numeros    if p else self.DEFAULT_NUMEROS
        mayusculas = p.requiere_mayusculas if p else self.DEFAULT_MAYUSCULAS
        simbolos   = p.requiere_simbolos   if p else self.DEFAULT_SIMBOLOS

        reglas = [f"mínimo {longitud} caracteres", "una minúscula"]
        if mayusculas: reglas.append("una mayúscula")
        if numeros:    reglas.append("un número")
        if simbolos:   reglas.append("un carácter especial")
        return "La contraseña debe tener: " + ", ".join(reglas) + "."
