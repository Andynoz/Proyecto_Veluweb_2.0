import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class CustomPasswordValidator:
    def validate(self, password, user=None):
        if not re.search(r"[A-Z]", password):
            raise ValidationError(_("La contraseña debe contener al menos una letra mayúscula."))

        if not re.search(r"[0-9]", password):
            raise ValidationError(_("La contraseña debe contener al menos un número."))

        if not re.search(r"[@$!%*?&]", password):
            raise ValidationError(_("La contraseña debe contener al menos un caracter especial (@, $, !, %, *, ?, &)."))

    def get_help_text(self):
        return _(
            "La contraseña debe tener al menos 8 caracteres, una mayúscula, un número y un caracter especial."
        )
