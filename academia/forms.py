from django import forms
from django.db.models import Q
from .models import (
    Abono, Adicional, CategoriaEgreso, Categoria, Comprobante, Curso, Egreso,
    Estudiante, EstudianteArchivado, JornadaCurso, Matricula, MatriculaArchivada,
    PersonaExterna, RecuperacionPendiente, Sede,
)


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'color', 'orden', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej.: Vacacionales'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'color': forms.Select(attrs={'class': 'form-input'}),
            'orden': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = [
            'categoria', 'nombre', 'descripcion',
            'ofrece_presencial', 'valor_presencial',
            'ofrece_online', 'valor_online',
            'duracion', 'numero_modulos', 'numero_modulos_online', 'activo',
        ]
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-input', 'id': 'id_categoria'}),
            'nombre': forms.TextInput(attrs={'class': 'form-input'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'valor_presencial': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0'}),
            'valor_online': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0'}),
            'duracion': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej.: 3 meses, 40 horas…'}),
            'numero_modulos': forms.NumberInput(attrs={
                'class': 'form-input', 'min': '1', 'max': '20', 'step': '1',
                'placeholder': 'Ej.: 4',
            }),
            'numero_modulos_online': forms.NumberInput(attrs={
                'class': 'form-input', 'min': '1', 'max': '20', 'step': '1',
                'placeholder': 'Ej.: 2',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = Categoria.objects.filter(activo=True)
        self.fields['categoria'].empty_label = '— Selecciona categoría —'

    def clean(self):
        cleaned = super().clean()
        ofrece_pres = cleaned.get('ofrece_presencial')
        ofrece_onl = cleaned.get('ofrece_online')
        if not ofrece_pres and not ofrece_onl:
            raise forms.ValidationError(
                'Debes seleccionar al menos una modalidad (presencial u online).'
            )
        return cleaned


class JornadaCursoForm(forms.ModelForm):
    """
    Form para crear/editar una jornada de un curso.
    El campo `descripcion` usa choices estandarizados, e incluye la opción
    'Otros' que habilita un campo de texto libre (`descripcion_otros`).
    La ciudad ahora se elige desde el catálogo de Sedes administrable.
    """
    class Meta:
        model = JornadaCurso
        fields = [
            'modalidad', 'descripcion', 'descripcion_otros', 'fecha_inicio',
            'hora_inicio', 'hora_fin', 'sede', 'activo',
        ]
        widgets = {
            'modalidad': forms.Select(attrs={'class': 'form-input'}),
            # ↓ Antes era TextInput, ahora es Select con los días estándar
            'descripcion': forms.Select(attrs={'class': 'form-input', 'id': 'id_descripcion_dias'}),
            'descripcion_otros': forms.TextInput(attrs={
                'class': 'form-input',
                'id': 'id_descripcion_otros',
                'placeholder': 'Ej. Viernes y Sábado',
            }),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'sede': forms.Select(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Placeholder limpio como primera opción del Select de días
        self.fields['descripcion'].widget.choices = [
            ('', '— Selecciona los días —'),
        ] + list(JornadaCurso._meta.get_field('descripcion').choices)

        # El selector de sede usa solo las sedes activas, más la que ya
        # tuviera la jornada (aunque esté desactivada) para no perderla al editar.
        sede_qs = Sede.objects.filter(activa=True)
        if self.instance and self.instance.pk and self.instance.sede_id:
            sede_qs = Sede.objects.filter(
                Q(activa=True) | Q(pk=self.instance.sede_id)
            )
        self.fields['sede'].queryset = sede_qs.distinct()
        self.fields['sede'].empty_label = '— Selecciona sede —'
        self.fields['sede'].required = False
        self.fields['descripcion_otros'].required = False

    def clean(self):
        cleaned_data = super().clean()
        modalidad = cleaned_data.get('modalidad')
        sede = cleaned_data.get('sede')
        descripcion = cleaned_data.get('descripcion')
        descripcion_otros = (cleaned_data.get('descripcion_otros') or '').strip()

        if modalidad == 'presencial' and not sede:
            self.add_error('sede', 'Debes seleccionar una sede para la modalidad presencial.')

        if descripcion == 'otros' and not descripcion_otros:
            self.add_error(
                'descripcion_otros',
                'Escribe los días personalizados cuando eliges "Otros".'
            )
        # Si no es "otros", limpiamos el texto libre para evitar datos sueltos
        if descripcion != 'otros':
            cleaned_data['descripcion_otros'] = ''

        return cleaned_data


class SedeForm(forms.ModelForm):
    """Form para que el admin cree/edite sedes desde el panel (sin tocar código)."""
    class Meta:
        model = Sede
        fields = ['nombre', 'pais', 'direccion', 'telefono', 'orden', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Ej. Guayaquil',
            }),
            'pais': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Ej. Ecuador',
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Dirección (opcional)',
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Teléfono (opcional)',
            }),
            'orden': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        labels = {
            'nombre': 'Nombre de la sede / ciudad',
            'pais': 'País',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
            'orden': 'Orden de aparición',
            'activa': 'Sede activa',
        }

    def clean_nombre(self):
        return (self.cleaned_data.get('nombre') or '').strip()

    def clean_pais(self):
        pais = (self.cleaned_data.get('pais') or '').strip()
        return pais or 'Ecuador'


class EstudianteForm(forms.ModelForm):
    # Campo extra (no del modelo): permite al usuario confirmar que quiere
    # usar un celular que ya pertenece a otro estudiante (familia, padres
    # que registran varios hijos con el mismo número, etc.).
    permitir_celular_duplicado = forms.BooleanField(
        required=False,
        label='Confirmo: número compartido (familia, hijos del mismo padre, etc.)',
        widget=forms.CheckboxInput(attrs={
            'id': 'id_est-permitir_celular_duplicado',
            'class': 'form-checkbox',
        }),
    )

    class Meta:
        model = Estudiante
        fields = [
            'cedula', 'apellidos', 'nombres', 'edad',
            'correo', 'celular', 'nivel_formacion',
            'titulo_profesional', 'ciudad',
        ]
        widgets = {
            'cedula': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '0102030405',
                'id': 'id_est-cedula',
                'autocomplete': 'off',
            }),
            'apellidos': forms.TextInput(attrs={'class': 'form-input'}),
            'nombres': forms.TextInput(attrs={'class': 'form-input'}),
            'edad': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'max': 120}),
            'correo': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'correo@ejemplo.com'}),
            'celular': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': '0991234567',
                'id': 'id_est-celular',
                'autocomplete': 'off',
            }),
            'nivel_formacion': forms.Select(attrs={'class': 'form-input'}),
            'titulo_profesional': forms.TextInput(attrs={'class': 'form-input'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-input'}),
        }

    def clean_celular(self):
        """
        Validación: si el celular ya pertenece a OTRO estudiante con cédula
        diferente, devolvemos un error claro indicando a quién pertenece,
        para evitar duplicados accidentales por confusión de números.

        El usuario puede marcar el checkbox "permitir_celular_duplicado"
        para confirmar que es intencional (familia, hijos, etc.) y saltarse
        esta validación.
        """
        celular = (self.cleaned_data.get('celular') or '').strip()
        if not celular:
            return celular  # opcional, se permite vacío

        # Si el usuario marcó el checkbox de "número compartido", se permite
        # el duplicado sin más preguntas. Leemos del POST crudo porque el
        # orden de procesamiento de los campos puede variar.
        permitir = self.data.get(self.add_prefix('permitir_celular_duplicado'))
        if permitir in ('on', 'true', 'True', '1', True):
            return celular

        cedula = (self.cleaned_data.get('cedula') or '').strip()
        qs = Estudiante.objects.filter(celular=celular)
        if cedula:
            # Si estamos editando o el mismo estudiante (misma cédula), no duplica
            qs = qs.exclude(cedula=cedula)
        # También excluir la propia instancia si existe
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        otro = qs.first()
        if otro:
            raise forms.ValidationError(
                f'⚠ Este número ya está registrado a {otro.nombre_completo} '
                f'(cédula {otro.cedula}). Si es un número compartido (familia, '
                f'hijos, etc.) marca la casilla "Confirmo: número compartido" '
                f'que aparece junto al campo y vuelve a guardar.'
            )
        return celular


class MatriculaForm(forms.ModelForm):
    """
    Formulario unificado de matrícula + comprobante.

    Cambios:
    - Acepta TODOS los cursos activos (no filtra por modalidad de URL).
      La modalidad final se infiere de la jornada elegida.
    - Acepta TODAS las jornadas activas del curso (presenciales + online).
    - Incluye `tipo_matricula` (Reserva/Abono, Reserva + Módulo 1, Programa Completo).
    - Incluye los datos de Comprobante: tipo_registro, factura, datos de factura,
      link al comprobante. La vendedora se asigna automáticamente desde
      request.user en la vista (no es un campo del form).
    """

    class Meta:
        model = Matricula
        fields = [
            # Datos académicos
            'curso', 'jornada',
            'estado', 'tipo_matricula',
            'fecha_matricula', 'talla_camiseta',
            'valor_curso', 'descuento', 'valor_pagado', 'observaciones',
            # Datos de comprobante
            'tipo_registro',
            'link_comprobante',
            'factura_realizada',
            'fact_nombres', 'fact_apellidos',
            'fact_cedula', 'fact_correo',
        ]
        widgets = {
            'curso': forms.Select(attrs={'class': 'form-input', 'id': 'id_curso'}),
            'jornada': forms.RadioSelect(attrs={'class': 'jornada-radio'}),
            'estado': forms.Select(attrs={
                'class': 'form-input', 'id': 'id_estado',
            }),
            'tipo_matricula': forms.Select(attrs={
                'class': 'form-input', 'id': 'id_tipo_matricula',
            }),
            'fecha_matricula': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}, format='%Y-%m-%d'),
            'talla_camiseta': forms.RadioSelect(attrs={'class': 'talla-radio'}),
            'valor_curso': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.01', 'id': 'id_valor_curso',
            }),
            'descuento': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.01', 'min': '0',
                'id': 'id_descuento', 'placeholder': '0.00',
            }),
            'valor_pagado': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.01', 'readonly': True,
            }),
            'observaciones': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            # Comprobante
            'tipo_registro': forms.Select(attrs={'class': 'form-input'}),
            'link_comprobante': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://… (Drive / Imgur / WhatsApp Web)',
            }),
            'factura_realizada': forms.Select(attrs={'class': 'form-input', 'id': 'id_factura_realizada'}),
            'fact_nombres': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombres del titular de factura',
            }),
            'fact_apellidos': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Apellidos del titular de factura',
            }),
            'fact_cedula': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Cédula / RUC',
            }),
            'fact_correo': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'correo@ejemplo.com',
            }),
        }

    def __init__(self, *args, modalidad='presencial', **kwargs):
        super().__init__(*args, **kwargs)
        self.modalidad = modalidad

        self.fields['valor_pagado'].initial = 0.00
        self.fields['valor_pagado'].help_text = (
            "Los pagos se registran posteriormente en la sección de Abonos."
        )

        # Cursos: TODOS los activos que ofrezcan al menos una modalidad.
        self.fields['curso'].queryset = Curso.objects.filter(
            activo=True,
        ).filter(Q(ofrece_presencial=True) | Q(ofrece_online=True))
        self.fields['curso'].empty_label = '— Selecciona un curso —'

        # Jornadas: TODAS las activas del curso (presenciales + online).
        if self.instance and self.instance.pk and self.instance.curso_id:
            self.fields['jornada'].queryset = JornadaCurso.objects.filter(
                curso_id=self.instance.curso_id,
                activo=True,
            )
        else:
            self.fields['jornada'].queryset = JornadaCurso.objects.filter(activo=True)

        # Tipo de registro: empty_label
        self.fields['tipo_registro'].empty_label = '— Selecciona origen —'

        # Required flags
        self.fields['jornada'].required = False
        self.fields['talla_camiseta'].required = False
        self.fields['tipo_matricula'].required = True
        self.fields['tipo_registro'].required = True
        self.fields['factura_realizada'].required = True

        # Tipo de matrícula: forzar que el usuario elija manualmente.
        # El modelo tiene default='programa_completo' pero en el formulario
        # queremos que aparezca vacío para que se elija conscientemente.
        self.fields['tipo_matricula'].initial = ''
        if hasattr(self.fields['tipo_matricula'], 'choices'):
            choices = list(self.fields['tipo_matricula'].choices)
            # Si la primera opción no es vacía, anteponemos una.
            if not choices or choices[0][0] != '':
                self.fields['tipo_matricula'].choices = (
                    [('', '— Selecciona el tipo de matrícula —')] + choices
                )
        # Si es una matrícula nueva (sin pk), nos aseguramos de que no
        # quede el default del modelo en el campo.
        if not (self.instance and self.instance.pk):
            if 'tipo_matricula' in self.initial:
                self.initial['tipo_matricula'] = ''
            self.fields['tipo_matricula'].widget.attrs.pop('value', None)

        # Descuento es opcional (default 0)
        self.fields['descuento'].required = False
        self.fields['descuento'].label = 'Descuento (USD)'
        self.fields['descuento'].help_text = (
            'Descuento opcional sobre el valor del curso. Se resta automáticamente '
            'del valor a pagar. Déjalo en 0 si no aplica.'
        )
        # Datos de factura: opcionales por defecto. Si factura_realizada == 'si',
        # los marcamos obligatorios en clean().
        for fname in ('fact_nombres', 'fact_apellidos', 'fact_cedula', 'fact_correo'):
            self.fields[fname].required = False
        self.fields['link_comprobante'].required = False

    def clean_descuento(self):
        """El descuento no puede ser negativo ni mayor al valor del curso."""
        from decimal import Decimal
        desc = self.cleaned_data.get('descuento') or Decimal('0.00')
        if desc < 0:
            raise forms.ValidationError('El descuento no puede ser negativo.')
        valor = self.cleaned_data.get('valor_curso')
        if valor is not None and desc > valor:
            raise forms.ValidationError(
                f'El descuento (${desc}) no puede ser mayor al valor del curso (${valor}).'
            )
        return desc

    def clean(self):
        cleaned = super().clean()
        # Si la factura está marcada como realizada, los datos de factura son obligatorios
        if cleaned.get('factura_realizada') == 'si':
            faltantes = []
            for fname, label in [
                ('fact_nombres', 'Nombres'),
                ('fact_apellidos', 'Apellidos'),
                ('fact_cedula', 'Cédula / RUC'),
                ('fact_correo', 'Correo'),
            ]:
                if not (cleaned.get(fname) or '').strip():
                    faltantes.append(label)
            if faltantes:
                raise forms.ValidationError(
                    'Si marcás "Factura realizada = Sí", debés llenar los datos '
                    'de factura: ' + ', '.join(faltantes) + '.'
                )
        return cleaned


class AbonoForm(forms.ModelForm):
    """Formulario para registrar/editar un pago (Abono / Pago Completo / Por Módulo / Recuperación)."""

    class Meta:
        model = Abono
        fields = [
            'fecha', 'monto', 'tipo_pago', 'numero_modulo',
            'cuenta_para_saldo',
            'metodo', 'banco',
            'numero_recibo', 'observaciones',
        ]
        widgets = {
            'fecha': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'monto': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.01', 'min': '0.01',
                'placeholder': '0.00',
            }),
            'tipo_pago': forms.Select(attrs={
                'class': 'form-input', 'id': 'id_tipo_pago',
            }),
            'numero_modulo': forms.Select(attrs={
                'class': 'form-input', 'id': 'id_numero_modulo',
            }),
            'cuenta_para_saldo': forms.Select(
                attrs={'class': 'form-input', 'id': 'id_cuenta_para_saldo'},
                choices=[
                    ('True', 'Sí — Sumar al pago del curso'),
                    ('False', 'No — Cobrar aparte (no afecta el saldo)'),
                ],
            ),
            'metodo': forms.Select(attrs={'class': 'form-input', 'id': 'id_metodo'}),
            'banco': forms.Select(attrs={'class': 'form-input', 'id': 'id_banco'}),
            'numero_recibo': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Se genera automáticamente si lo dejas vacío',
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 2,
                'placeholder': 'Detalles del pago, referencia bancaria, etc.',
            }),
        }
        labels = {
            'tipo_pago': 'Tipo de pago',
            'numero_modulo': 'Módulo',
            'cuenta_para_saldo': '¿Suma al pago del curso?',
            'numero_recibo': 'Nº de recibo',
            'banco': 'Banco',
        }

    def __init__(self, *args, matricula=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.matricula = matricula
        self.fields['numero_recibo'].required = False
        self.fields['banco'].required = False
        self.fields['banco'].empty_label = '— Selecciona un banco —'
        self.fields['numero_modulo'].required = False

        # Construir choices de módulos según el curso de la matrícula
        modulo_choices = [('', '— Selecciona módulo —')]
        if matricula and matricula.curso_id:
            n = matricula.curso.get_numero_modulos(matricula.modalidad)
            modulo_choices += [(i, f'Módulo {i}') for i in range(1, n + 1)]
        else:
            # Fallback genérico
            modulo_choices += [(i, f'Módulo {i}') for i in range(1, 6)]
        self.fields['numero_modulo'].widget.choices = modulo_choices

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto is not None and monto <= 0:
            raise forms.ValidationError('El monto debe ser mayor a cero.')
        return monto

    def clean(self):
        cleaned = super().clean()
        monto = cleaned.get('monto')
        metodo = cleaned.get('metodo')
        banco = cleaned.get('banco')
        tipo_pago = cleaned.get('tipo_pago') or 'abono'
        numero_modulo = cleaned.get('numero_modulo')
        cuenta = cleaned.get('cuenta_para_saldo')
        # cuenta_para_saldo viene como string 'True'/'False' por el Select widget;
        # Django convierte 'True'/'False' al BooleanField, pero por seguridad:
        if isinstance(cuenta, str):
            cuenta = cuenta.lower() in ('true', '1', 'sí', 'si', 'yes')
            cleaned['cuenta_para_saldo'] = cuenta

        # Si NO es recuperación, siempre cuenta para saldo
        if tipo_pago != 'recuperacion':
            cleaned['cuenta_para_saldo'] = True

        # Si tipo es por_modulo o recuperacion, el módulo es obligatorio
        if tipo_pago in ('por_modulo', 'recuperacion') and not numero_modulo:
            self.add_error('numero_modulo',
                           'Debes seleccionar un módulo para este tipo de pago.')

        # Validar que el número de módulo esté en rango [1..n_mod] del curso.
        # Solo aplica cuando el tipo de pago realmente usa el módulo. Para
        # tipos abono/pago_completo el módulo se ignora (se limpia abajo),
        # así que no tiene sentido bloquear el envío por un valor que no
        # va a guardarse. La UI ya previene módulos inválidos en el
        # <select>; esta validación protege contra envíos manipulados.
        if (tipo_pago in ('por_modulo', 'recuperacion')
                and numero_modulo
                and self.matricula and self.matricula.curso_id):
            n_mod_curso = self.matricula.curso.get_numero_modulos(self.matricula.modalidad)
            if not (1 <= numero_modulo <= n_mod_curso):
                self.add_error(
                    'numero_modulo',
                    f'El módulo {numero_modulo} no existe. Este curso tiene '
                    f'{n_mod_curso} módulo(s); elige uno entre 1 y {n_mod_curso}.'
                )

        # Si tipo es abono o pago_completo, el módulo se limpia
        if tipo_pago in ('abono', 'pago_completo'):
            cleaned['numero_modulo'] = None

        if metodo == 'transferencia' and not banco:
            raise forms.ValidationError({
                'banco': 'Debes indicar el banco cuando el método es Transferencia.'
            })
        if metodo == 'tarjeta' and not banco:
            raise forms.ValidationError({
                'banco': 'Debes indicar la opción correspondiente (Payphone).'
            })

        if metodo not in ['transferencia', 'tarjeta']:
            cleaned['banco'] = ''

        # Validación de saldo: solo aplica si el pago cuenta para el saldo del curso.
        # Recuperaciones cobradas APARTE no se validan contra el saldo.
        if (self.matricula and monto and
                cleaned.get('cuenta_para_saldo', True)):
            from decimal import Decimal
            valor_neto = self.matricula.valor_neto
            otros = self.matricula.abonos.filter(cuenta_para_saldo=True)
            if self.instance and self.instance.pk:
                otros = otros.exclude(pk=self.instance.pk)
            total_otros = sum((a.monto for a in otros), Decimal('0.00'))
            if total_otros + monto > valor_neto:
                disponible = valor_neto - total_otros
                raise forms.ValidationError(
                    f'El monto excede el saldo. Máximo permitido: ${disponible:.2f} '
                    f'(valor a pagar ${valor_neto:.2f} − ya pagado ${total_otros:.2f}). '
                    f'Si es una clase de recuperación que se cobra aparte, '
                    f'cambia "¿Suma al pago del curso?" a "No".'
                )
        return cleaned


# ─────────────────────────────────────────────────────────
# Comprobante de Venta
# ─────────────────────────────────────────────────────────

class ComprobanteForm(forms.ModelForm):
    """
    Formulario de Comprobante de Venta.
    TODOS los campos son obligatorios (según requerimiento).
    El campo `vendedora` NO se incluye: se asigna automáticamente
    desde request.user en la vista.
    """

    class Meta:
        model = Comprobante
        fields = [
            'curso', 'modalidad', 'fecha_inscripcion',
            'nombre_persona', 'celular',
            'tipo_registro',
            'pago_abono', 'diferencia',
            'link_comprobante',
            'jornada', 'inicio_curso',
            'factura_realizada',
            'fact_nombres', 'fact_apellidos',
            'fact_cedula', 'fact_correo',
        ]
        widgets = {
            'curso': forms.Select(attrs={
                'class': 'form-input', 'required': 'required',
            }),
            'modalidad': forms.Select(attrs={
                'class': 'form-input', 'required': 'required',
            }),
            'fecha_inscripcion': forms.DateInput(attrs={
                'class': 'form-input', 'type': 'date', 'required': 'required',
            }),
            'nombre_persona': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Nombre completo del cliente',
                'required': 'required',
            }),
            'celular': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': '0991234567',
                'required': 'required',
            }),
            'tipo_registro': forms.Select(attrs={
                'class': 'form-input', 'required': 'required',
            }),
            'pago_abono': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.01', 'min': '0',
                'placeholder': '0.00', 'required': 'required',
            }),
            'diferencia': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.01', 'min': '0',
                'placeholder': '0.00', 'required': 'required',
            }),
            'link_comprobante': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://… (opcional)',
            }),
            'jornada': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej.: Sábados 08:00–12:00',
                'required': 'required',
            }),
            'inicio_curso': forms.DateInput(attrs={
                'class': 'form-input', 'type': 'date', 'required': 'required',
            }),
            'factura_realizada': forms.Select(attrs={
                'class': 'form-input', 'required': 'required',
            }),
            'fact_nombres': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Nombres del titular de factura',
                'required': 'required',
            }),
            'fact_apellidos': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Apellidos del titular de factura',
                'required': 'required',
            }),
            'fact_cedula': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Cédula / RUC',
                'required': 'required',
            }),
            'fact_correo': forms.EmailInput(attrs={
                'class': 'form-input', 'placeholder': 'correo@ejemplo.com',
                'required': 'required',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['curso'].queryset = Curso.objects.filter(activo=True)
        self.fields['curso'].empty_label = '— Selecciona un curso —'
        self.fields['tipo_registro'].empty_label = '— Selecciona tipo —'

        OPCIONALES = {'link_comprobante'}
        for name, field in self.fields.items():
            field.required = name not in OPCIONALES

    def clean_celular(self):
        cel = (self.cleaned_data.get('celular') or '').strip()
        if not cel:
            raise forms.ValidationError('El celular es obligatorio.')
        return cel

    def clean_pago_abono(self):
        valor = self.cleaned_data.get('pago_abono')
        if valor is None or valor < 0:
            raise forms.ValidationError('El pago o abono debe ser un valor válido (≥ 0).')
        return valor

    def clean_diferencia(self):
        valor = self.cleaned_data.get('diferencia')
        if valor is None or valor < 0:
            raise forms.ValidationError('La diferencia debe ser un valor válido (≥ 0).')
        return valor


# ─────────────────────────────────────────────────────────
# Registro Administrativo: Egresos
# ─────────────────────────────────────────────────────────

class EgresoForm(forms.ModelForm):
    """Formulario para registrar/editar un egreso (gasto)."""

    class Meta:
        model = Egreso
        fields = ['fecha', 'categoria', 'concepto', 'monto', 'notas']
        widgets = {
            'fecha': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'categoria': forms.Select(attrs={'class': 'form-input'}),
            'concepto': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej.: Sueldo Mayo - Ana López',
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.01', 'min': '0.01',
                'placeholder': '0.00',
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 3,
                'placeholder': 'Nº de factura, beneficiario, referencia bancaria…',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = CategoriaEgreso.objects.filter(activo=True)
        self.fields['categoria'].empty_label = '— Selecciona categoría —'

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto is not None and monto <= 0:
            raise forms.ValidationError('El monto debe ser mayor a cero.')
        return monto


class CategoriaEgresoForm(forms.ModelForm):
    class Meta:
        model = CategoriaEgreso
        fields = ['nombre', 'descripcion', 'color', 'icono', 'orden', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'color': forms.Select(attrs={'class': 'form-input'}),
            'icono': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': '💼',
                'maxlength': '4',
            }),
            'orden': forms.NumberInput(attrs={'class': 'form-input'}),
        }


# ─────────────────────────────────────────────────────────
# Recuperación de clases
# ─────────────────────────────────────────────────────────

class RecuperacionPendienteForm(forms.ModelForm):
    """
    Formulario para marcar una clase a recuperación.
    Se usa en la edición de matrícula y en el listado de pagos.
    """
    class Meta:
        model = RecuperacionPendiente
        fields = ['numero_modulo', 'fecha_marcada', 'observaciones']
        widgets = {
            'numero_modulo': forms.Select(attrs={'class': 'form-input'}),
            'fecha_marcada': forms.DateInput(attrs={
                'class': 'form-input', 'type': 'date',
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 2,
                'placeholder': 'Motivo de la falta, fecha de recuperación pactada, etc.',
            }),
        }
        labels = {
            'numero_modulo': 'Módulo de la clase a recuperar',
            'fecha_marcada': 'Fecha de la falta',
        }

    def __init__(self, *args, matricula=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.matricula = matricula
        # Construir choices según el curso
        choices = [('', '— Selecciona módulo —')]
        if matricula and matricula.curso_id:
            n = matricula.curso.get_numero_modulos(matricula.modalidad)
            choices += [(i, f'Módulo {i}') for i in range(1, n + 1)]
        else:
            choices += [(i, f'Módulo {i}') for i in range(1, 6)]
        self.fields['numero_modulo'].widget.choices = choices
        self.fields['observaciones'].required = False


# ─────────────────────────────────────────────────────────
# Adicional: Certificados, Examen Supletorio, Camisas extra
# ─────────────────────────────────────────────────────────

class PersonaExternaForm(forms.ModelForm):
    """
    Formulario para registrar/editar a una persona EXTERNA a la academia
    (alguien que compra un certificado, examen supletorio o camisa
    sin estar matriculado).
    """
    class Meta:
        model = PersonaExterna
        fields = [
            'cedula', 'apellidos', 'nombres',
            'correo', 'celular', 'ciudad', 'observaciones',
        ]
        widgets = {
            'cedula': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Ej.: 0912345678',
                'autocomplete': 'off',
            }),
            'apellidos': forms.TextInput(attrs={'class': 'form-input'}),
            'nombres': forms.TextInput(attrs={'class': 'form-input'}),
            'correo': forms.EmailInput(attrs={'class': 'form-input'}),
            'celular': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': '0991234567',
            }),
            'ciudad': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Ej.: Guayaquil',
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 2,
                'placeholder': 'Notas adicionales sobre esta persona (opcional).',
            }),
        }
        labels = {
            'cedula': 'Cédula *',
            'apellidos': 'Apellidos *',
            'nombres': 'Nombres *',
            'correo': 'Correo (opcional)',
            'celular': 'Celular (opcional)',
            'ciudad': 'Ciudad (opcional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo cédula, apellidos y nombres son obligatorios
        self.fields['correo'].required = False
        self.fields['celular'].required = False
        self.fields['ciudad'].required = False
        self.fields['observaciones'].required = False

    def clean_cedula(self):
        cedula = (self.cleaned_data.get('cedula') or '').strip()
        if not cedula:
            return cedula

        # Validar que no sea un estudiante ya registrado
        if Estudiante.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError(
                'Esta cédula ya pertenece a un ESTUDIANTE matriculado. '
                'Debes registrar el adicional en la opción "Estudiante Interno".'
            )
        if _buscar_estudiante_archivado(cedula):
            raise forms.ValidationError(
                'Esta cédula pertenece a un ESTUDIANTE archivado. '
                'Debes registrar el adicional en la opción "Estudiante Interno"; '
                'el sistema lo recuperará del archivo al guardar.'
            )

        # Si estamos creando, validar que no exista otra persona externa
        if not self.instance.pk and PersonaExterna.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError('Ya existe una persona externa registrada con esta cédula.')

        return cedula


class _AdicionalBaseForm(forms.ModelForm):
    """
    Base común para los formularios de adicional (interno y externo).
    Maneja la lógica condicional de campos según el tipo_adicional.
    """
    class Meta:
        model = Adicional
        fields = [
            'tipo_adicional',
            'curso', 'modalidad',
            'talla_camiseta',
            'numero_modulo',
            'fecha', 'valor', 'metodo_pago', 'banco',
            'numero_recibo',
            'factura_realizada',
            'fact_nombres', 'fact_apellidos', 'fact_cedula', 'fact_correo',
            'observaciones',
        ]
        widgets = {
            'tipo_adicional': forms.Select(attrs={
                'class': 'form-input', 'id': 'id_tipo_adicional',
            }),
            'curso': forms.Select(attrs={'class': 'form-input'}),
            'modalidad': forms.Select(attrs={'class': 'form-input'}),
            'talla_camiseta': forms.Select(attrs={'class': 'form-input'}),
            'numero_modulo': forms.NumberInput(attrs={
                'class': 'form-input', 'min': 1, 'max': 10,
                'placeholder': 'Ej.: 1',
            }),
            'fecha': forms.DateInput(attrs={
                'class': 'form-input', 'type': 'date',
            }),
            'valor': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.01', 'min': '0',
                'placeholder': 'Ej.: 15.00',
            }),
            'metodo_pago': forms.Select(attrs={'class': 'form-input', 'id': 'id_metodo_pago'}),
            'banco': forms.Select(attrs={'class': 'form-input', 'id': 'id_banco'}),
            'numero_recibo': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Se genera automáticamente si lo dejas vacío',
            }),
            'factura_realizada': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_factura_realizada',
            }),
            'fact_nombres': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombres del titular de factura',
            }),
            'fact_apellidos': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Apellidos del titular de factura',
            }),
            'fact_cedula': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Cédula / RUC',
            }),
            'fact_correo': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'correo@ejemplo.com',
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 2,
            }),
        }
        labels = {
            'tipo_adicional': 'Tipo de adicional *',
            'curso': 'Curso (si aplica)',
            'modalidad': 'Modalidad del curso',
            'talla_camiseta': 'Talla de camiseta',
            'numero_modulo': 'Módulo del examen supletorio',
            'fecha': 'Fecha *',
            'valor': 'Valor (USD) *',
            'metodo_pago': 'Método de pago *',
            'banco': 'Banco',
            'numero_recibo': 'Nº de recibo',
            'factura_realizada': '¿Factura realizada? *',
            'fact_nombres': 'Nombres',
            'fact_apellidos': 'Apellidos',
            'fact_cedula': 'Número de cédula / RUC',
            'fact_correo': 'Correo electrónico',
            'observaciones': 'Observaciones',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo cursos activos en el desplegable
        self.fields['curso'].queryset = Curso.objects.filter(activo=True).order_by('nombre')
        self.fields['curso'].required = False
        self.fields['curso'].empty_label = '— Sin curso —'

        self.fields['modalidad'].required = False
        self.fields['modalidad'].choices = [
            ('', '— Sin modalidad —'),
            ('presencial', 'Presencial'),
            ('online', 'Online'),
        ]

        self.fields['talla_camiseta'].required = False
        self.fields['talla_camiseta'].choices = [
            ('', '— Sin talla —')
        ] + list(Adicional.TALLAS_CAMISETA)

        self.fields['numero_modulo'].required = False
        self.fields['banco'].required = False
        self.fields['banco'].empty_label = '— Selecciona un banco —'
        self.fields['numero_recibo'].required = False
        self.fields['factura_realizada'].required = True
        for fname in ('fact_nombres', 'fact_apellidos', 'fact_cedula', 'fact_correo'):
            self.fields[fname].required = False
        self.fields['observaciones'].required = False

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo_adicional')
        curso = cleaned.get('curso')
        modalidad = cleaned.get('modalidad')
        talla = cleaned.get('talla_camiseta')
        metodo = cleaned.get('metodo_pago')
        banco = cleaned.get('banco')
        factura = cleaned.get('factura_realizada')

        # Validación de banco según método
        if metodo == 'transferencia' and not banco:
            self.add_error('banco', 'Debes indicar el banco cuando el método es Transferencia.')
        if metodo == 'tarjeta' and not banco:
            self.add_error('banco', 'Debes indicar la opción correspondiente (Payphone).')
        if metodo not in ['transferencia', 'tarjeta']:
            cleaned['banco'] = ''

        # Validaciones según tipo
        if tipo in ('cert_matricula', 'cert_asistencia', 'cert_antiguo', 'examen_supletorio'):
            if not curso:
                self.add_error('curso', 'Selecciona el curso al que se refiere este adicional.')
            if not modalidad:
                self.add_error('modalidad', 'Indica si era presencial u online.')

        if tipo == 'camisa':
            if not talla:
                self.add_error('talla_camiseta', 'Selecciona la talla de la camisa.')

        if factura == 'si':
            faltantes = []
            for fname, label in (
                ('fact_nombres', 'Nombres'),
                ('fact_apellidos', 'Apellidos'),
                ('fact_cedula', 'Cédula / RUC'),
                ('fact_correo', 'Correo'),
            ):
                if not cleaned.get(fname):
                    self.add_error(fname, 'Este dato es obligatorio cuando la factura está realizada.')
                    faltantes.append(label)
            if faltantes:
                self.add_error(
                    None,
                    'Si marcas "Factura realizada = Sí", debes llenar los datos de factura: '
                    + ', '.join(faltantes) + '.'
                )

        return cleaned


def _nivel_formacion_codigo(valor):
    valor = (valor or '').strip()
    if not valor:
        return ''
    for codigo, label in Estudiante.NIVELES_FORMACION:
        if valor == codigo or valor == label:
            return codigo
    return ''


def _edad_entera(valor):
    if valor in (None, ''):
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _buscar_estudiante_archivado(cedula):
    archivado = (
        EstudianteArchivado.objects
        .filter(cedula=cedula)
        .order_by('-archivado_en')
        .first()
    )
    if archivado:
        return archivado
    return (
        MatriculaArchivada.objects
        .filter(cedula=cedula)
        .order_by('-archivado_en')
        .first()
    )


def _crear_estudiante_desde_archivo(archivado):
    ciudad = getattr(archivado, 'ciudad', getattr(archivado, 'ciudad_estudiante', '')) or ''
    titulo = getattr(archivado, 'titulo_profesional', '') or ''
    return Estudiante.objects.create(
        cedula=archivado.cedula,
        apellidos=archivado.apellidos,
        nombres=archivado.nombres,
        edad=_edad_entera(getattr(archivado, 'edad', None)),
        correo=archivado.correo or '',
        celular=archivado.celular or '',
        nivel_formacion=_nivel_formacion_codigo(getattr(archivado, 'nivel_formacion', '')),
        titulo_profesional=titulo,
        ciudad=ciudad,
    )


class AdicionalInternoForm(_AdicionalBaseForm):
    """
    Formulario para crear un Adicional para un ESTUDIANTE INTERNO de la academia.
    Selecciona el estudiante por cédula (con autocompletar).
    """
    cedula_estudiante = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Cédula del estudiante',
            'autocomplete': 'off',
            'id': 'id_cedula_estudiante',
        }),
        label='Cédula del estudiante *',
        help_text='Escribe la cédula y se autocompletarán los datos.',
    )

    def clean_cedula_estudiante(self):
        cedula = (self.cleaned_data.get('cedula_estudiante') or '').strip()
        if not cedula:
            raise forms.ValidationError('Debes ingresar la cédula del estudiante.')
        try:
            est = Estudiante.objects.get(cedula=cedula)
        except Estudiante.DoesNotExist:
            archivado = _buscar_estudiante_archivado(cedula)
            if not archivado:
                raise forms.ValidationError(
                    'No existe un estudiante con esa cédula. '
                    'Si la persona no está matriculada, registra el adicional como "Persona externa".'
                )
            self.estudiante_obj = None
            self.estudiante_archivado_obj = archivado
            return cedula
        self.estudiante_obj = est
        self.estudiante_archivado_obj = None
        return cedula

    def save(self, commit=True):
        instance = super().save(commit=False)
        estudiante = getattr(self, 'estudiante_obj', None)
        if estudiante is None:
            archivado = getattr(self, 'estudiante_archivado_obj', None)
            if archivado:
                estudiante = (
                    Estudiante.objects.filter(cedula=archivado.cedula).first()
                    or _crear_estudiante_desde_archivo(archivado)
                )
        instance.estudiante = estudiante
        instance.persona_externa = None
        if commit:
            instance.save()
        return instance


class AdicionalExternoForm(_AdicionalBaseForm):
    """
    Formulario para crear un Adicional para una PERSONA EXTERNA.
    Permite seleccionar una persona externa ya registrada (por cédula).
    Si no existe, hay que registrarla primero.
    """
    cedula_externa = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Cédula de la persona externa',
            'autocomplete': 'off',
            'id': 'id_cedula_externa',
        }),
        label='Cédula de la persona externa *',
        help_text='La persona debe estar registrada previamente. Si no existe, regístrala primero.',
    )

    def clean_cedula_externa(self):
        cedula = (self.cleaned_data.get('cedula_externa') or '').strip()
        if not cedula:
            raise forms.ValidationError('Debes ingresar la cédula de la persona.')
        try:
            persona = PersonaExterna.objects.get(cedula=cedula)
        except PersonaExterna.DoesNotExist:
            raise forms.ValidationError(
                'No existe una persona externa con esa cédula. '
                'Regístrala primero en "+ Registrar Persona Externa".'
            )
        self.persona_obj = persona
        return cedula

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.persona_externa = getattr(self, 'persona_obj', None)
        instance.estudiante = None
        if commit:
            instance.save()
        return instance


class AdicionalSupletorioRapidoForm(forms.Form):
    """
    Formulario rápido para crear un Adicional tipo 'examen_supletorio'
    desde la vista de pagos de una matrícula. Solo pide módulo, fecha y valor.
    El estudiante, curso, modalidad y matricula_origen se infieren de la matrícula.
    """
    METODOS_PAGO = Adicional.METODOS_PAGO

    numero_modulo = forms.IntegerField(
        min_value=1, max_value=10,
        widget=forms.Select(attrs={'class': 'form-input'}),
        label='Módulo del examen supletorio *',
    )
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-input', 'type': 'date',
        }),
        label='Fecha del cobro *',
    )
    valor = forms.DecimalField(
        max_digits=10, decimal_places=2, min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input', 'step': '0.01', 'min': '0',
            'placeholder': 'Ej.: 15.00',
        }),
        label='Valor del examen supletorio (USD) *',
    )
    metodo_pago = forms.ChoiceField(
        choices=METODOS_PAGO,
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_metodo_pago'}),
        label='Método de pago *',
        initial='efectivo',
    )
    banco = forms.ChoiceField(
        choices=[('', '— Selecciona un banco —')] + Abono.BANCOS,
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_banco'}),
        label='Banco',
        required=False,
    )
    numero_recibo = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Se genera automáticamente si lo dejas vacío',
        }),
        label='Nº de recibo',
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input', 'rows': 2,
            'placeholder': 'Notas adicionales (opcional).',
        }),
        label='Observaciones',
    )

    def __init__(self, *args, matricula=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.matricula = matricula
        # Construir choices del módulo según el curso
        choices = [('', '— Selecciona módulo —')]
        if matricula and matricula.curso_id:
            n = matricula.curso.get_numero_modulos(matricula.modalidad)
            choices += [(i, f'Módulo {i}') for i in range(1, n + 1)]
        else:
            choices += [(i, f'Módulo {i}') for i in range(1, 6)]
        self.fields['numero_modulo'].widget.choices = choices

    def clean(self):
        cleaned = super().clean()
        metodo = cleaned.get('metodo_pago')
        banco = cleaned.get('banco')

        if metodo == 'transferencia' and not banco:
            self.add_error('banco', 'Debes indicar el banco cuando el método es Transferencia.')
        if metodo == 'tarjeta' and not banco:
            self.add_error('banco', 'Debes indicar la opción correspondiente (Payphone).')
        if metodo not in ['transferencia', 'tarjeta']:
            cleaned['banco'] = ''

        return cleaned
