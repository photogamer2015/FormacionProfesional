from django.db import models
from decimal import Decimal


# ─────────────────────────────────────────────────────────
# Constantes compartidas
# ─────────────────────────────────────────────────────────

MODALIDADES = [
    ('presencial', 'Presencial'),
    ('online', 'Online'),
]

# Días estandarizados para JornadaCurso.descripcion
# (los códigos son cortos para guardar en BD; los labels se muestran al usuario)
JORNADA_DIAS = [
    ('lun_mie_vie', 'Lun, Mié, Vie.'),
    ('mar_mie_jue', 'Mar, Mié, Jue.'),
    ('mar_jue', 'Martes y Jueves'),
    ('sabados_intensivos', 'Sábados Intensivos'),
    ('domingos_intensivos', 'Domingos Intensivos'),
    ('otros', 'Otros (especificar)'),
]

# Tipos de matrícula contratada por el estudiante
TIPO_MATRICULA = [
    ('reserva_abono', 'Reserva / Abono'),
    ('reserva_modulo_1', 'Reserva + Módulo 1'),
    ('programa_completo', 'Programa Completo'),
]

# Estados de la matrícula
ESTADOS_MATRICULA = [
    ('activa', 'Activa'),
    ('retiro_voluntario', 'Retiro voluntario'),
]

# Tipo de registro (canal/origen de la venta)
TIPOS_REGISTRO = [
    ('central_1', 'Central 1'),
    ('central_2', 'Central 2'),
    ('central_ia', 'Central IA'),
    ('seguimiento', 'Seguimiento'),
]

# Sí / No (para "factura realizada")
SI_NO = [
    ('si', 'Sí'),
    ('no', 'No'),
]


# ─────────────────────────────────────────────────────────
# Sede / Campus (administrable por admin, sin tocar código)
# ─────────────────────────────────────────────────────────

class Sede(models.Model):
    """
    Campus o sede física donde se dictan las jornadas presenciales.

    El administrador puede crear/editar/desactivar sedes desde el panel
    sin tocar el código. Esto permite que el software escale a nuevos
    países o ciudades (ej. Caracas, Venezuela) de forma autónoma.

    Las sedes se agrupan por país para mantener todo organizado cuando
    se opera en varios países a la vez.
    """
    nombre = models.CharField(
        max_length=100,
        help_text='Nombre de la sede o ciudad (ej. Guayaquil, Quito, Caracas).'
    )
    pais = models.CharField(
        max_length=80, default='Ecuador',
        help_text='País donde está la sede (ej. Ecuador, Venezuela).'
    )
    direccion = models.CharField(
        max_length=200, blank=True,
        help_text='Dirección física de la sede (opcional).'
    )
    telefono = models.CharField(
        max_length=40, blank=True,
        help_text='Teléfono de contacto de la sede (opcional).'
    )
    orden = models.PositiveIntegerField(
        default=0,
        help_text='Orden de aparición en los listados (menor primero).'
    )
    activa = models.BooleanField(
        default=True,
        help_text='Si está desactivada, no aparece para elegir en jornadas nuevas, '
                  'pero las jornadas existentes que ya la usan se conservan.'
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sede / Campus'
        verbose_name_plural = 'Sedes / Campus'
        ordering = ['pais', 'orden', 'nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['nombre', 'pais'],
                name='sede_unica_nombre_pais',
            )
        ]

    @property
    def etiqueta(self):
        """Nombre legible para mostrar (ej. 'Guayaquil · Ecuador')."""
        if self.pais and self.pais.strip().lower() != 'ecuador':
            return f'{self.nombre} · {self.pais}'
        return self.nombre

    def __str__(self):
        return self.etiqueta


class Categoria(models.Model):
    """
    Categoría de cursos. Por defecto: Empresariales, Técnico, Vacacionales.
    Pero el usuario puede agregar las que quiera.
    """
    COLORES = [
        ('#1a237e', 'Azul'),
        ('#2e7d32', 'Verde'),
        ('#c62828', 'Rojo'),
        ('#f0ad4e', 'Naranja'),
        ('#6a1b9a', 'Morado'),
        ('#00838f', 'Cian'),
        ('#5d4037', 'Marrón'),
        ('#455a64', 'Gris'),
    ]

    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.TextField(blank=True)
    color = models.CharField(
        max_length=7, choices=COLORES, default='#1a237e',
        help_text='Color con el que se identifica la categoría.'
    )
    orden = models.PositiveIntegerField(
        default=0,
        help_text='Orden de aparición (menor = primero).'
    )
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class Curso(models.Model):
    """
    Cursos que se ofertan. Cada uno puede ofrecerse en modalidad presencial,
    online, o en ambas. Cada modalidad tiene su propio valor.
    """

    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT,
        related_name='cursos', null=True, blank=True,
    )
    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.TextField(blank=True)

    # Modalidades que ofrece el curso
    ofrece_presencial = models.BooleanField(
        default=True,
        help_text='Marcar si el curso se ofrece en modalidad presencial.'
    )
    ofrece_online = models.BooleanField(
        default=False,
        help_text='Marcar si el curso se ofrece en modalidad online.'
    )

    # Valores diferenciados por modalidad
    valor_presencial = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text='Costo del curso presencial (USD).'
    )
    valor_online = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text='Costo del curso online (USD).'
    )

    # Campo legado (se conserva para no romper datos antiguos).
    valor = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text='[Legado] Valor único anterior. Reemplazado por valor_presencial / valor_online.'
    )

    duracion = models.CharField(max_length=100, blank=True)

    # Número de módulos del programa. Configurable por curso.
    # Por defecto: 4 (presencial típico). El usuario lo ajusta:
    #  - Online estándar: 2 módulos
    #  - Online de Tributación / Asistente Contable / Talento Humano: 1 módulo
    #  - Presencial estándar: 4 módulos (algunos llegan a 5)
    numero_modulos = models.PositiveIntegerField(
        default=4,
        help_text='Cantidad de módulos para modalidad PRESENCIAL. Se usa para el control de pagos por módulo.'
    )
    numero_modulos_online = models.PositiveIntegerField(
        default=2,
        help_text='Cantidad de módulos para modalidad ONLINE. Se usa para el control de pagos por módulo.'
    )

    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['categoria__orden', 'nombre']

    def lista_modulos(self):
        """Devuelve [1, 2, 3, ...] hasta numero_modulos (presencial, usado por legacy)."""
        n = self.numero_modulos or 1
        return list(range(1, n + 1))

    def get_numero_modulos(self, modalidad):
        """Devuelve la cantidad de módulos según la modalidad."""
        if modalidad == 'online':
            return self.numero_modulos_online or 1
        return self.numero_modulos or 1

    def valor_para(self, modalidad):
        """Devuelve el valor del curso según la modalidad."""
        if modalidad == 'online':
            return self.valor_online
        return self.valor_presencial

    def ofrece(self, modalidad):
        """¿El curso se ofrece en esa modalidad?"""
        if modalidad == 'online':
            return self.ofrece_online
        return self.ofrece_presencial

    @property
    def modalidades_etiqueta(self):
        """Texto corto que indica las modalidades disponibles."""
        partes = []
        if self.ofrece_presencial:
            partes.append('Presencial')
        if self.ofrece_online:
            partes.append('Online')
        return ' + '.join(partes) if partes else '— Sin modalidad —'

    def __str__(self):
        v = self.valor_presencial if self.ofrece_presencial else self.valor_online
        return f'{self.nombre} (${v})'

    @property
    def jornadas_presencial_count(self):
        return self.jornadas.filter(modalidad='presencial', activo=True).count()

    @property
    def jornadas_online_count(self):
        return self.jornadas.filter(modalidad='online', activo=True).count()


class JornadaCurso(models.Model):
    """
    Cada curso puede tener varias jornadas (días + horario + ciudad/zona).
    Estas son las opciones que el estudiante elige al matricularse.
    Cada jornada pertenece a una modalidad (presencial u online).
    """
    curso = models.ForeignKey(
        Curso, on_delete=models.CASCADE, related_name='jornadas'
    )
    modalidad = models.CharField(
        max_length=20, choices=MODALIDADES, default='presencial',
        help_text='Modalidad de esta jornada.'
    )
    descripcion = models.CharField(
        max_length=200, choices=JORNADA_DIAS,
        help_text='Días en que se dicta la jornada.'
    )
    descripcion_otros = models.CharField(
        max_length=120, blank=True,
        help_text='Días personalizados (solo se usa cuando la descripción es "Otros").'
    )
    fecha_inicio = models.DateField()
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)
    sede = models.ForeignKey(
        'Sede', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='jornadas',
        help_text='Sede/campus donde se dicta (presencial). Reemplaza al texto libre de ciudad.'
    )
    ciudad = models.CharField(
        max_length=100, blank=True,
        help_text='Ciudad (presencial) o plataforma (online). Se mantiene sincronizada con la sede.'
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Jornada'
        verbose_name_plural = 'Jornadas'
        ordering = ['curso', 'modalidad', 'fecha_inicio']

    @property
    def descripcion_legible(self):
        """Devuelve el label del choice (Lun, Mié, Vie. etc.), el texto
        personalizado si es 'Otros', o el valor crudo si es legado."""
        if self.descripcion == 'otros':
            return self.descripcion_otros.strip() or 'Otros días'
        # get_descripcion_display() devuelve el label si está en choices,
        # o el valor crudo si quedó algún registro legado fuera de los choices.
        return self.get_descripcion_display()

    @property
    def etiqueta(self):
        prefijo = '🟢 Online' if self.modalidad == 'online' else '🏫 Presencial'
        partes = [prefijo, self.descripcion_legible]
        if self.fecha_inicio:
            partes.append(self.fecha_inicio.strftime('%d/%m/%Y'))
        if self.hora_inicio and self.hora_fin:
            partes.append(
                f'{self.hora_inicio.strftime("%H:%M")} a {self.hora_fin.strftime("%H:%M")}'
            )
        if self.ciudad:
            partes.append(f'({self.ciudad})')
        return ' – '.join(partes)

    @property
    def sede_nombre(self):
        """Nombre de la sede para mostrar: usa la FK si existe, si no el texto ciudad."""
        if self.sede_id:
            return self.sede.nombre
        return self.ciudad or ''

    def save(self, *args, **kwargs):
        # Mantener el campo de texto `ciudad` sincronizado con la sede elegida,
        # para que toda la lógica existente que filtra/muestra por `ciudad`
        # (exports, control por módulo, archivado, etc.) siga funcionando.
        if self.sede_id:
            self.ciudad = self.sede.nombre
        super().save(*args, **kwargs)

    def __str__(self):
        return self.etiqueta


class Estudiante(models.Model):
    """Datos personales del estudiante."""

    NIVELES_FORMACION = [
        ('primaria', 'Primaria'),
        ('secundaria', 'Bachillerato / Secundaria'),
        ('tecnico', 'Técnico'),
        ('tecnologo', 'Tecnólogo'),
        ('tercer_nivel', 'Tercer Nivel (Pregrado)'),
        ('cuarto_nivel', 'Cuarto Nivel (Posgrado)'),
        ('otro', 'Otro'),
    ]

    cedula = models.CharField(max_length=20, unique=True)
    apellidos = models.CharField(max_length=100)
    nombres = models.CharField(max_length=100)
    edad = models.PositiveIntegerField(null=True, blank=True)
    correo = models.EmailField(blank=True)
    celular = models.CharField(max_length=20, blank=True)
    nivel_formacion = models.CharField(
        max_length=20, choices=NIVELES_FORMACION, blank=True
    )
    titulo_profesional = models.CharField(max_length=200, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
        ordering = ['apellidos', 'nombres']

    @property
    def nombre_completo(self):
        return f'{self.apellidos} {self.nombres}'.strip()

    @property
    def celular_wa(self):
        """Limpia el número de celular para usar en enlaces wa.me."""
        c = (self.celular or '').strip()
        digitos = ''.join(x for x in c if x.isdigit())
        if not digitos:
            return ""
        if digitos.startswith('0') and len(digitos) == 10:
            return '593' + digitos[1:]
        if digitos.startswith('593'):
            return digitos
        return digitos

    def __str__(self):
        return f'{self.cedula} – {self.nombre_completo}'


class Matricula(models.Model):
    """Matrícula que une estudiante + curso + jornada + pago."""

    TALLAS_CAMISETA = [
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('NA', 'Ninguna de las anteriores (la academia solo cubre hasta XL)'),
    ]

    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.PROTECT, related_name='matriculas'
    )
    curso = models.ForeignKey(
        Curso, on_delete=models.PROTECT, related_name='matriculas'
    )
    jornada = models.ForeignKey(
        JornadaCurso, on_delete=models.PROTECT,
        related_name='matriculas', null=True, blank=True,
        help_text='Fecha y horario seleccionados (depende del curso y modalidad).'
    )
    modalidad = models.CharField(
        max_length=20, choices=MODALIDADES, default='presencial'
    )
    estado = models.CharField(
        max_length=20, choices=ESTADOS_MATRICULA, default='activa',
        help_text='Estado académico de la matrícula.'
    )
    tipo_matricula = models.CharField(
        max_length=30, choices=TIPO_MATRICULA, default='programa_completo',
        help_text='Tipo de matrícula contratada por el estudiante.'
    )
    fecha_matricula = models.DateField()
    talla_camiseta = models.CharField(
        max_length=2, choices=TALLAS_CAMISETA, blank=True
    )
    valor_curso = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text='Se autocompleta con el valor del curso según modalidad, pero puedes ajustarlo.'
    )
    descuento = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text='Descuento aplicado al valor del curso (USD). Opcional.'
    )
    valor_pagado = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00')
    )
    observaciones = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    # Auditoría: qué usuario registró la matrícula
    registrado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='matriculas_registradas',
        help_text='Usuario que registró la matrícula (admin o asesor). '
                  'Se usa también como vendedor/a en el comprobante asociado.'
    )

    # ── Comprobante de venta (datos integrados desde el módulo Comprobantes) ──
    # La matrícula incluye los campos que antes vivían sólo en Comprobante
    # y al guardarse genera/actualiza un Comprobante espejo para el ranking.
    tipo_registro = models.CharField(
        max_length=20, choices=TIPOS_REGISTRO, blank=True,
        help_text='Origen del registro: Central 1, Central 2, Central IA o Seguimiento.'
    )
    factura_realizada = models.CharField(
        max_length=2, choices=SI_NO, default='no',
        help_text='¿Se emitió factura para esta matrícula?'
    )
    fact_nombres = models.CharField(
        max_length=120, blank=True,
        help_text='Nombres del titular de la factura.'
    )
    fact_apellidos = models.CharField(
        max_length=120, blank=True,
        help_text='Apellidos del titular de la factura.'
    )
    fact_cedula = models.CharField(
        max_length=20, blank=True,
        help_text='Cédula o RUC para la factura.'
    )
    fact_correo = models.EmailField(
        blank=True,
        help_text='Correo electrónico para enviar la factura.'
    )
    link_comprobante = models.URLField(
        max_length=500, blank=True,
        help_text='Link a la foto del comprobante de pago (Drive, Imgur, WhatsApp Web, etc.).'
    )

    class Meta:
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'
        ordering = ['-fecha_matricula', '-creado']

    @property
    def valor_neto(self):
        """Valor del curso con descuento aplicado. Es lo que realmente debe pagar el estudiante."""
        valor = self.valor_curso or Decimal('0.00')
        desc = self.descuento or Decimal('0.00')
        neto = valor - desc
        return neto if neto > 0 else Decimal('0.00')

    @property
    def tiene_descuento(self):
        return (self.descuento or Decimal('0.00')) > 0

    @property
    def saldo(self):
        if self.estado == 'retiro_voluntario':
            return Decimal('0.00')
        return self.valor_neto - (self.valor_pagado or Decimal('0.00'))

    @property
    def estado_pago(self):
        if self.estado == 'retiro_voluntario':
            return 'Retiro'
        if self.saldo <= 0:
            return 'Pagado'
        if self.valor_pagado and self.valor_pagado > 0:
            return 'Parcial'
        return 'Pendiente'

    @property
    def horario(self):
        if self.jornada and self.jornada.hora_inicio and self.jornada.hora_fin:
            return f'{self.jornada.hora_inicio.strftime("%H:%M")} – {self.jornada.hora_fin.strftime("%H:%M")}'
        return '—'

    @property
    def sede(self):
        if self.jornada and self.jornada.ciudad:
            return self.jornada.ciudad
        return '—'

    def recalcular_valor_pagado(self, save=True):
        """
        Recalcula valor_pagado como la suma de todos los abonos
        (excluyendo los pagos de recuperación que se cobran APARTE).
        Se llama automáticamente al guardar/eliminar un Abono.
        """
        # Solo cuenta para saldo los abonos donde cuenta_para_saldo=True
        # (las recuperaciones cobradas APARTE no suman al valor pagado del curso).
        total = self.abonos.filter(cuenta_para_saldo=True).aggregate(
            s=models.Sum('monto')
        )['s'] or Decimal('0.00')
        self.valor_pagado = total
        if save:
            super().save(update_fields=['valor_pagado', 'actualizado'])
        return total

    # ── Helpers para el control por módulo ──
    def pagos_por_modulo(self):
        from collections import defaultdict
        resultado = defaultdict(lambda: Decimal('0.00'))
        for a in self.abonos.filter(
            cuenta_para_saldo=True,
            numero_modulo__isnull=False,
        ):
            resultado[a.numero_modulo] += a.monto
        return dict(resultado)

    def pagos_por_modulo_efectivo(self):
        n_mod = (self.curso.get_numero_modulos(self.modalidad) if self.curso_id else 1) or 1
        if n_mod <= 0:
            return {}

        valor_modulo = (
            self.valor_neto / Decimal(n_mod) if n_mod > 0 else Decimal('0.00')
        )

        aplicado = {n: Decimal('0.00') for n in range(1, n_mod + 1)}

        libre_total = Decimal('0.00')
        for a in self.abonos.filter(cuenta_para_saldo=True):
            if a.numero_modulo and 1 <= a.numero_modulo <= n_mod:
                aplicado[a.numero_modulo] += a.monto
            else:
                libre_total += a.monto

        carry = Decimal('0.00')
        for n in range(1, n_mod + 1):
            if aplicado[n] < valor_modulo:
                falta = valor_modulo - aplicado[n]
                tomar_carry = min(falta, carry)
                aplicado[n] += tomar_carry
                carry -= tomar_carry
                falta -= tomar_carry
                if falta > 0 and libre_total > 0:
                    tomar_libre = min(falta, libre_total)
                    aplicado[n] += tomar_libre
                    libre_total -= tomar_libre

            if aplicado[n] > valor_modulo and valor_modulo > 0:
                carry += aplicado[n] - valor_modulo
                aplicado[n] = valor_modulo

        remanente = carry + libre_total
        if remanente > 0 and n_mod >= 1:
            aplicado[n_mod] += remanente

        return aplicado

    def desglose_pagos_por_modulo(self):
        n_mod = (self.curso.get_numero_modulos(self.modalidad) if self.curso_id else 1) or 1
        if n_mod <= 0:
            return []

        # IMPORTANTE: redondeamos valor_modulo a 2 decimales porque los pagos
        # reales solo pueden tener 2 decimales (USD). Si dejáramos el valor
        # con todos sus decimales (ej. 100/3 = 33.33333...), un módulo
        # pagado con $33.33 quedaría como "Parcial" para siempre — el
        # estudiante nunca podría completarlo. Al redondear, la suma de
        # los n_mod módulos puede quedar 1 centavo arriba o abajo del
        # valor neto; eso es aceptable para el control por módulo. El
        # saldo total real sigue calculándose desde valor_pagado.
        if n_mod > 0:
            valor_modulo = (self.valor_neto / Decimal(n_mod)).quantize(Decimal('0.01'))
        else:
            valor_modulo = Decimal('0.00')

        aplicado = {n: Decimal('0.00') for n in range(1, n_mod + 1)}
        fecha_ultimo = {n: None for n in range(1, n_mod + 1)}

        for a in self.abonos.filter(
            cuenta_para_saldo=True,
            tipo_pago__in=('por_modulo', 'recuperacion'),
            numero_modulo__isnull=False,
        ).order_by('fecha', 'creado'):
            n = a.numero_modulo
            if not (1 <= n <= n_mod):
                continue
            aplicado[n] += a.monto
            if fecha_ultimo[n] is None or a.fecha > fecha_ultimo[n]:
                fecha_ultimo[n] = a.fecha

        desglose = []
        # Si el estudiante ya canceló TODO el curso (saldo total <= 0), todos
        # los módulos se muestran como "Pagado", sin importar cómo se haya
        # distribuido el dinero entre módulos (pago único, abono libre, etc.).
        # Esto evita el caso confuso de pagar todo en un módulo y que el resto
        # siga apareciendo como "Pendiente".
        curso_pagado_total = self.saldo <= 0 and self.estado != 'retiro_voluntario'

        for n in range(1, n_mod + 1):
            pagado = aplicado[n]
            if curso_pagado_total:
                estado = 'Pagado'
            elif pagado >= valor_modulo and valor_modulo > 0:
                estado = 'Pagado'
            elif pagado > 0:
                estado = 'Parcial'
            else:
                estado = 'Pendiente'
            desglose.append({
                'numero': n,
                'pagado': pagado,
                'esperado': valor_modulo,
                'estado': estado,
                'fecha_ultimo_pago': fecha_ultimo[n],
            })
        return desglose

    def estado_modulo(self, numero_modulo, valor_modulo=None, pagos_efectivos=None):
        if valor_modulo is None:
            n_mod = self.curso.get_numero_modulos(self.modalidad) if self.curso_id else 1
            n_mod = n_mod or 1
            valor_modulo = self.valor_neto / Decimal(n_mod)

        if pagos_efectivos is None:
            pagos_efectivos = self.pagos_por_modulo_efectivo()
        pagado = pagos_efectivos.get(numero_modulo, Decimal('0.00'))

        # Si el curso está totalmente pagado (saldo <= 0), cualquier módulo
        # se considera "Pagado" — coherente con desglose_pagos_por_modulo().
        if self.saldo <= 0 and self.estado != 'retiro_voluntario':
            estado = 'Pagado'
        elif pagado >= valor_modulo and valor_modulo > 0:
            estado = 'Pagado'
        elif pagado > 0:
            estado = 'Parcial'
        else:
            estado = 'Pendiente'
        return estado, pagado, valor_modulo

    def save(self, *args, **kwargs):
        if self.jornada_id:
            try:
                jornada_modalidad = self.jornada.modalidad
                if jornada_modalidad:
                    self.modalidad = jornada_modalidad
            except JornadaCurso.DoesNotExist:
                pass

        if not self.valor_curso and self.curso_id:
            self.valor_curso = self.curso.valor_para(self.modalidad)
        super().save(*args, **kwargs)

        try:
            self._sync_comprobante()
        except Exception:
            pass

    def _sync_comprobante(self):
        if not self.registrado_por_id:
            return

        modalidad_comp = 'virtual' if self.modalidad == 'online' else 'presencial'

        nombre_persona = (
            f'{self.estudiante.apellidos} {self.estudiante.nombres}'.strip()
            if self.estudiante_id else ''
        )
        celular = self.estudiante.celular if self.estudiante_id else ''
        fact_nombres = self.fact_nombres or (self.estudiante.nombres if self.estudiante_id else '')
        fact_apellidos = self.fact_apellidos or (self.estudiante.apellidos if self.estudiante_id else '')
        fact_cedula = self.fact_cedula or (self.estudiante.cedula if self.estudiante_id else '')
        fact_correo = self.fact_correo or (self.estudiante.correo if self.estudiante_id else '') or ''

        defaults = {
            'curso': self.curso,
            'modalidad': modalidad_comp,
            'fecha_inscripcion': self.fecha_matricula,
            'jornada': (self.jornada.descripcion_legible if self.jornada_id else ''),
            'inicio_curso': (self.jornada.fecha_inicio if self.jornada_id and self.jornada.fecha_inicio else self.fecha_matricula),
            'nombre_persona': nombre_persona,
            'celular': celular,
            'tipo_registro': self.tipo_registro or None,
            'pago_abono': self.valor_pagado or Decimal('0.00'),
            'diferencia': self.saldo if self.saldo > 0 else Decimal('0.00'),
            'link_comprobante': self.link_comprobante or '',
            'vendedora': self.registrado_por,
            'vendedora_nombre': (
                f'{self.registrado_por.first_name} {self.registrado_por.last_name}'.strip()
                or self.registrado_por.username
            ),
            'factura_realizada': self.factura_realizada or 'no',
            'fact_nombres': fact_nombres,
            'fact_apellidos': fact_apellidos,
            'fact_cedula': fact_cedula,
            'fact_correo': fact_correo,
        }

        comp = Comprobante.objects.filter(matricula=self).first()
        if comp:
            for k, v in defaults.items():
                setattr(comp, k, v)
            comp.save()
        else:
            Comprobante.objects.create(matricula=self, **defaults)

    def __str__(self):
        return f'{self.estudiante} – {self.curso} ({self.get_modalidad_display()})'


# ─────────────────────────────────────────────────────────
# Abonos / Pagos
# ─────────────────────────────────────────────────────────

class Abono(models.Model):
    """Registro de un pago/abono realizado por un estudiante.

    Este modelo se usa extensamente en vistas y formularios. Se mantiene
    sencillo pero con los campos necesarios: fecha, monto, tipo de pago,
    módulo asociado (opcional), si cuenta para saldo, método y banco.
    """

    TIPOS_PAGO = [
        ('abono', 'Abono'),
        ('por_modulo', 'Por módulo'),
        ('pago_completo', 'Pago completo'),
        ('recuperacion', 'Recuperación'),
    ]

    METODOS = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia bancaria'),
        ('tarjeta', 'Tarjeta'),
    ]

    BANCOS = [
        ('pichincha', 'Pichincha'),
        ('guayaquil', 'Guayaquil'),
        ('produbanco', 'Produbanco'),
        ('banco_pacifico', 'Banco del Pacífico'),
        ('payphone', 'Payphone'),
    ]

    matricula = models.ForeignKey(
        Matricula, on_delete=models.CASCADE, related_name='abonos'
    )
    fecha = models.DateField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_pago = models.CharField(max_length=20, choices=TIPOS_PAGO, default='abono')
    numero_modulo = models.PositiveIntegerField(null=True, blank=True)
    cuenta_para_saldo = models.BooleanField(default=True)
    metodo = models.CharField(max_length=20, choices=METODOS, default='efectivo')
    banco = models.CharField(max_length=30, choices=BANCOS, blank=True)
    numero_recibo = models.CharField(max_length=30, unique=True, blank=True)
    observaciones = models.TextField(blank=True)

    registrado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='abonos_registrados'
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Abono'
        verbose_name_plural = 'Abonos'
        ordering = ['-fecha', '-creado']

    @staticmethod
    def generar_numero_recibo():
        """Genera el siguiente número de recibo correlativo: REC-0001, REC-0002..."""
        ultimo = Abono.objects.filter(
            numero_recibo__startswith='REC-'
        ).order_by('-numero_recibo').first()

        if ultimo and ultimo.numero_recibo[4:].isdigit():
            siguiente = int(ultimo.numero_recibo[4:]) + 1
        else:
            siguiente = 1
        return f'REC-{siguiente:04d}'

    def save(self, *args, **kwargs):
        if not self.numero_recibo:
            self.numero_recibo = Abono.generar_numero_recibo()
        super().save(*args, **kwargs)
        if self.matricula_id:
            self.matricula.recalcular_valor_pagado()

    def delete(self, *args, **kwargs):
        matricula = self.matricula
        super().delete(*args, **kwargs)
        matricula.recalcular_valor_pagado()

    def __str__(self):
        return f'{self.numero_recibo} — {self.matricula.estudiante.nombre_completo} — ${self.monto}'


class AssistantQueryLog(models.Model):
    """Registro de consultas al asistente (chatbot).

    Se usa para analizar preguntas frecuentes y mejorar reglas/prompts.
    """
    user = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL)
    path = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    reply = models.TextField(blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de consulta asistente'
        verbose_name_plural = 'Registros de consultas asistente'
        ordering = ['-created']

    def __str__(self):
        user = self.user.username if self.user else 'anon'
        return f'{self.created:%Y-%m-%d %H:%M} | {user} | {self.message[:40]}'


class RecuperacionPendiente(models.Model):
    """Clase marcada como recuperación (falta de clase) pendiente de cobro/recuperación."""

    matricula = models.ForeignKey(
        Matricula, on_delete=models.CASCADE, related_name='recuperaciones_pendientes'
    )
    numero_modulo = models.PositiveIntegerField(
        help_text='Módulo de la clase que se debe recuperar.'
    )
    fecha_marcada = models.DateField(
        help_text='Fecha en que se marcó la clase a recuperar.'
    )
    saldo_pendiente_al_marcar = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text='Saldo que el estudiante tenía pendiente al momento de marcar la recuperación. Se arrastra para mostrarlo cuando se cobre la recuperación.'
    )
    pagada = models.BooleanField(
        default=False, help_text='True cuando el estudiante ya recuperó la clase y se cobró.'
    )

    fecha_recuperacion = models.DateField(
        null=True, blank=True,
        help_text='Fecha en que efectivamente recuperó la clase.'
    )
    abono = models.OneToOneField(
        'Abono', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recuperacion',
        help_text='Pago asociado a esta recuperación (si ya se cobró).'
    )
    observaciones = models.TextField(blank=True)

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Clase en recuperación'
        verbose_name_plural = 'Clases en recuperación'
        ordering = ['pagada', '-fecha_marcada', '-creado']

    def __str__(self):
        estado = 'Pagada' if self.pagada else 'Pendiente'
        return f'{self.matricula.estudiante.nombre_completo} – Mód. {self.numero_modulo} ({estado})'


# ─────────────────────────────────────────────────────────
# Comprobante de Venta
# ─────────────────────────────────────────────────────────

class Comprobante(models.Model):
    """
    Comprobante de venta registrado por una vendedora/asesora.

    Captura datos completos del cliente, curso vendido, pago/abono y datos
    para la facturación. Sirve para llevar el ranking de ventas por asesora.
    """

    MODALIDAD_OPCIONES = [
        ('virtual', 'Virtual'),
        ('presencial', 'Presencial'),
    ]

    SI_NO = [
        ('si', 'Sí'),
        ('no', 'No'),
    ]

    TIPOS_REGISTRO = [
        ('central_1', 'Central 1'),
        ('central_2', 'Central 2'),
        ('central_ia', 'Central IA'),
        ('seguimiento', 'Seguimiento'),
    ]

    # ── Datos del curso vendido ──────────────────────────
    curso = models.ForeignKey(
        Curso, on_delete=models.PROTECT,
        related_name='comprobantes',
        verbose_name='Curso',
    )
    # ── Vínculo con Matrícula (nuevo: comprobantes generados desde matrículas) ──
    # Es nullable para no romper los comprobantes legados creados antes
    # de la unificación de los dos módulos.
    matricula = models.OneToOneField(
        'Matricula', on_delete=models.CASCADE,
        related_name='comprobante',
        null=True, blank=True,
        verbose_name='Matrícula vinculada',
        help_text='Si el comprobante se generó automáticamente desde una matrícula, '
                  'aquí queda el vínculo. Si fue cargado manualmente desde el '
                  'módulo Comprobantes, queda vacío.',
    )
    modalidad = models.CharField(
        max_length=20, choices=MODALIDAD_OPCIONES,
        verbose_name='Modalidad',
    )
    fecha_inscripcion = models.DateField(
        verbose_name='Fecha de inscripción',
    )
    jornada = models.CharField(
        max_length=200,
        verbose_name='Jornada',
        help_text='Ej.: Sábados 08:00–12:00, Domingos intensivos…',
    )
    inicio_curso = models.DateField(
        verbose_name='Inicio del curso',
    )

    # ── Datos del cliente ────────────────────────────────
    nombre_persona = models.CharField(
        max_length=200,
        verbose_name='Nombre de la persona',
    )
    celular = models.CharField(
        max_length=20,
        verbose_name='Celular',
    )

    # ── Tipo de Registro ─────────────────────────────────
    tipo_registro = models.CharField(
        max_length=20, choices=TIPOS_REGISTRO, blank=True, null=True,
        verbose_name='Tipo de registro',
        help_text='Origen del registro: Central 1, Central 2, Central IA o Seguimiento.'
    )

    # ── Pagos ────────────────────────────────────────────
    pago_abono = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Pago o abono (USD)',
        help_text='Monto recibido al momento de la venta.',
    )
    diferencia = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Diferencia (USD)',
        help_text='Saldo pendiente.',
    )
    link_comprobante = models.URLField(
        max_length=500, blank=True,
        verbose_name='Link del comprobante',
        help_text='Link a la foto del comprobante (Drive, Imgur, WhatsApp Web, etc.). Opcional.',
    )

    # ── Vendedora / Asesora ──────────────────────────────
    vendedora = models.ForeignKey(
        'auth.User', on_delete=models.PROTECT,
        related_name='comprobantes_registrados',
        verbose_name='Vendedora',
        help_text='Asesor/admin que registró la venta. Se asigna automáticamente.',
    )
    vendedora_nombre = models.CharField(
        max_length=150, blank=True,
        verbose_name='Nombre de la vendedora (registro)',
    )

    # ── Factura ──────────────────────────────────────────
    factura_realizada = models.CharField(
        max_length=2, choices=SI_NO, default='no',
        verbose_name='Factura realizada',
    )

    fact_nombres = models.CharField(
        max_length=120,
        verbose_name='Nombres (factura)',
    )
    fact_apellidos = models.CharField(
        max_length=120,
        verbose_name='Apellidos (factura)',
    )
    fact_cedula = models.CharField(
        max_length=20,
        verbose_name='Número de cédula (factura)',
    )
    fact_correo = models.EmailField(
        verbose_name='Correo electrónico (factura)',
    )

    # ── Auditoría ────────────────────────────────────────
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Comprobante'
        verbose_name_plural = 'Comprobantes'
        ordering = ['-fecha_inscripcion', '-creado']

    @property
    def total_venta(self):
        from decimal import Decimal
        pago = self.pago_abono or Decimal('0.00')
        dif = self.diferencia or Decimal('0.00')
        return pago + dif

    @property
    def estado_pago(self):
        from decimal import Decimal
        if (self.diferencia or Decimal('0.00')) <= 0:
            return 'Pagado'
        if (self.pago_abono or Decimal('0.00')) > 0:
            return 'Parcial'
        return 'Pendiente'

    def save(self, *args, **kwargs):
        if not self.vendedora_nombre and self.vendedora_id:
            full = f'{self.vendedora.first_name} {self.vendedora.last_name}'.strip()
            self.vendedora_nombre = full or self.vendedora.username
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Comprobante #{self.pk} — {self.nombre_persona} ({self.curso.nombre})'


# ─────────────────────────────────────────────────────────
# Registro Administrativo: Egresos / Pérdidas
# ─────────────────────────────────────────────────────────

class CategoriaEgreso(models.Model):
    """
    Categoría de gasto/egreso. Se usa para clasificar los egresos
    en el módulo de Registro Administrativo.
    """
    COLORES = [
        ('#c62828', 'Rojo'),
        ('#f0ad4e', 'Naranja'),
        ('#1a237e', 'Azul'),
        ('#2e7d32', 'Verde'),
        ('#6a1b9a', 'Morado'),
        ('#00838f', 'Cian'),
        ('#5d4037', 'Marrón'),
        ('#455a64', 'Gris'),
    ]

    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.TextField(blank=True)
    color = models.CharField(
        max_length=7, choices=COLORES, default='#c62828',
    )
    icono = models.CharField(
        max_length=4, blank=True,
        help_text='Emoji corto para mostrar (ej.: 💼, 🏠, 💡, 📦).'
    )
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Categoría de egreso'
        verbose_name_plural = 'Categorías de egresos'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class Egreso(models.Model):
    """
    Cada gasto registrado por el administrador en el módulo
    de Registro Administrativo.
    """

    fecha = models.DateField(
        help_text='Fecha en que se efectuó el gasto.'
    )
    categoria = models.ForeignKey(
        CategoriaEgreso, on_delete=models.PROTECT,
        related_name='egresos',
    )
    concepto = models.CharField(
        max_length=200,
        help_text='Descripción corta del gasto (ej.: "Sueldo Mayo - Ana").'
    )
    monto = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Monto del gasto en USD.'
    )
    notas = models.TextField(
        blank=True,
        help_text='Detalles adicionales: nº de factura, beneficiario, referencia, etc.'
    )

    registrado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='egresos_registrados',
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Egreso'
        verbose_name_plural = 'Egresos'
        ordering = ['-fecha', '-creado']

    def __str__(self):
        return f'{self.fecha} — {self.concepto} (${self.monto})'


# ─────────────────────────────────────────────────────────
# Alertas de pago (control de morosidad temprana)
# ─────────────────────────────────────────────────────────

class AlertaPagoRevisada(models.Model):
    """
    Registro de qué alertas de pago pendiente ya fueron revisadas u ocultadas
    por la asesora/administrador durante un día específico.

    Uso: cuando una asesora ve una alerta en el dashboard y la descarta
    (porque ya llamó al estudiante, ya fue gestionada, etc.), se crea un
    registro aquí para no volver a mostrar esa alerta el mismo día.
    Al día siguiente vuelve a aparecer si el módulo sigue impago, dándole
    a la asesora una nueva oportunidad de gestionar el cobro.
    """

    matricula = models.ForeignKey(
        'Matricula', on_delete=models.CASCADE,
        related_name='alertas_revisadas',
    )
    numero_modulo = models.PositiveIntegerField(
        help_text='Módulo cuya alerta fue revisada.'
    )
    fecha = models.DateField(
        help_text='Día en que la alerta fue marcada como revisada.'
    )
    revisada_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='alertas_revisadas',
    )
    notas = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Alerta de pago revisada'
        verbose_name_plural = 'Alertas de pago revisadas'
        unique_together = [('matricula', 'numero_modulo', 'fecha')]
        ordering = ['-fecha', '-creado']

    def __str__(self):
        return f'Alerta Mód.{self.numero_modulo} — {self.matricula} ({self.fecha})'


# ─────────────────────────────────────────────────────────
# Adicional: Certificados, Examen Supletorio, Camisas extra
# ─────────────────────────────────────────────────────────

class PersonaExterna(models.Model):
    """
    Personas que NO son estudiantes de la academia pero compran
    algún servicio adicional (ej.: una camisa, un certificado antiguo
    de un curso pasado, examen supletorio externo, etc.).
    """
    cedula = models.CharField(max_length=20, unique=True)
    apellidos = models.CharField(max_length=100)
    nombres = models.CharField(max_length=100)
    correo = models.EmailField(blank=True)
    celular = models.CharField(max_length=20, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    observaciones = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Persona externa'
        verbose_name_plural = 'Personas externas'
        ordering = ['apellidos', 'nombres']

    @property
    def nombre_completo(self):
        return f'{self.apellidos} {self.nombres}'.strip()

    def __str__(self):
        return f'{self.cedula} – {self.nombre_completo} (externo)'


class Adicional(models.Model):
    """
    Registro de servicios/productos ADICIONALES vendidos:
    certificados (matrícula, asistencia, antiguo), examen supletorio
    y camisas extra. La persona puede ser un Estudiante (interno)
    o una PersonaExterna.

    Estos ingresos suman al total del mes en el dashboard administrativo
    y aparecen como un KPI separado con el "+".

    El valor lo define libremente el usuario (no hay precio fijo).
    """

    TIPOS_ADICIONAL = [
        ('cert_matricula', 'Certificado de matrícula'),
        ('cert_asistencia', 'Certificado de asistencia'),
        ('cert_antiguo', 'Certificado antiguo'),
        ('examen_supletorio', 'Examen supletorio'),
        ('camisa', 'Camisa'),
    ]

    TALLAS_CAMISETA = [
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('NA', 'Ninguna de las anteriores (la academia solo cubre hasta XL)'),
    ]

    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia bancaria'),
        ('tarjeta', 'Tarjeta de crédito/débito'),
    ]

    # ── Tipo de adicional ──
    tipo_adicional = models.CharField(
        max_length=30, choices=TIPOS_ADICIONAL,
        help_text='Tipo de servicio/producto adicional.'
    )

    # ── Persona (uno de los dos) ──
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.PROTECT,
        related_name='adicionales',
        null=True, blank=True,
        help_text='Estudiante interno de la academia.'
    )
    persona_externa = models.ForeignKey(
        PersonaExterna, on_delete=models.PROTECT,
        related_name='adicionales',
        null=True, blank=True,
        help_text='Persona externa a la academia.'
    )

    # ── Datos del curso (relevante para certificados y examen supletorio) ──
    curso = models.ForeignKey(
        Curso, on_delete=models.PROTECT,
        related_name='adicionales',
        null=True, blank=True,
        help_text='Curso al que se refiere el certificado o examen. '
                  'No aplica para camisas.'
    )
    modalidad = models.CharField(
        max_length=20, choices=MODALIDADES, blank=True,
        help_text='Modalidad del curso (presencial/online).'
    )

    # ── Datos para CAMISA ──
    talla_camiseta = models.CharField(
        max_length=2, choices=TALLAS_CAMISETA, blank=True,
        help_text='Solo aplica si tipo_adicional = camisa.'
    )

    # ── Datos para EXAMEN SUPLETORIO ──
    matricula_origen = models.ForeignKey(
        Matricula, on_delete=models.SET_NULL,
        related_name='adicionales_supletorios',
        null=True, blank=True,
        help_text='Matrícula desde la que se generó el examen supletorio '
                  '(si se marcó desde el detalle de pagos).'
    )
    numero_modulo = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Módulo del examen supletorio.'
    )

    # ── Pago ──
    fecha = models.DateField(
        help_text='Fecha en que se cobró el adicional.'
    )
    valor = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text='Valor del adicional (USD). El usuario lo define libremente.'
    )
    metodo_pago = models.CharField(
        max_length=20, choices=METODOS_PAGO, default='efectivo',
        help_text='Forma de pago.'
    )
    banco = models.CharField(
        max_length=20, choices=Abono.BANCOS, blank=True,
        help_text='Banco usado (solo si el método es Transferencia bancaria o Tarjeta).'
    )
    numero_recibo = models.CharField(
        max_length=30, unique=True, blank=True,
        help_text='Número de comprobante. Si se deja vacío, se genera automáticamente.'
    )

    # ── Factura ──────────────────────────────────────────
    factura_realizada = models.CharField(
        max_length=2, choices=SI_NO, default='no',
        help_text='¿Se emitió factura para este adicional?'
    )
    fact_nombres = models.CharField(
        max_length=120, blank=True,
        help_text='Nombres del titular de la factura.'
    )
    fact_apellidos = models.CharField(
        max_length=120, blank=True,
        help_text='Apellidos del titular de la factura.'
    )
    fact_cedula = models.CharField(
        max_length=20, blank=True,
        help_text='Cédula o RUC para la factura.'
    )
    fact_correo = models.EmailField(
        blank=True,
        help_text='Correo electrónico para enviar la factura.'
    )

    observaciones = models.TextField(blank=True)

    # ── Auditoría ──
    registrado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='adicionales_registrados',
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Adicional'
        verbose_name_plural = 'Adicionales'
        ordering = ['-fecha', '-creado']

    @staticmethod
    def generar_numero_recibo():
        """Genera el siguiente número de recibo correlativo: ADC-0001, ADC-0002..."""
        ultimo = Adicional.objects.filter(
            numero_recibo__startswith='ADC-'
        ).order_by('-numero_recibo').first()

        if ultimo and ultimo.numero_recibo[4:].isdigit():
            siguiente = int(ultimo.numero_recibo[4:]) + 1
        else:
            siguiente = 1
        return f'ADC-{siguiente:04d}'

    def save(self, *args, **kwargs):
        if not self.numero_recibo:
            self.numero_recibo = Adicional.generar_numero_recibo()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.numero_recibo} — ${self.valor} ({self.fecha})'

    # ── Helpers ──

    @property
    def es_externo(self):
        return self.persona_externa_id is not None

    @property
    def es_interno(self):
        return self.estudiante_id is not None

    @property
    def persona_nombre(self):
        if self.es_interno and self.estudiante_id:
            return self.estudiante.nombre_completo
        if self.es_externo and self.persona_externa_id:
            return self.persona_externa.nombre_completo
        return '—'

    @property
    def persona_cedula(self):
        if self.es_interno and self.estudiante_id:
            return self.estudiante.cedula
        if self.es_externo and self.persona_externa_id:
            return self.persona_externa.cedula
        return '—'

    @property
    def persona_celular(self):
        if self.es_interno and self.estudiante_id:
            return self.estudiante.celular or ''
        if self.es_externo and self.persona_externa_id:
            return self.persona_externa.celular or ''
        return ''

    @property
    def origen_label(self):
        return 'Estudiante interno' if self.es_interno else (
            'Persona externa' if self.es_externo else 'Sin asignar'
        )

    @property
    def tipo_icono(self):
        ICONOS = {
            'cert_matricula': '📜',
            'cert_asistencia': '✅',
            'cert_antiguo': '🗂️',
            'examen_supletorio': '📝',
            'camisa': '👕',
        }
        return ICONOS.get(self.tipo_adicional, '➕')

    @property
    def detalle_corto(self):
        """Texto compacto para listas: tipo + curso/talla."""
        partes = [self.get_tipo_adicional_display()]
        if self.tipo_adicional == 'camisa' and self.talla_camiseta:
            partes.append(f'Talla {self.talla_camiseta}')
        elif self.curso_id:
            partes.append(self.curso.nombre)
            if self.modalidad:
                partes.append(self.get_modalidad_display())
        if self.tipo_adicional == 'examen_supletorio' and self.numero_modulo:
            partes.append(f'Mód. {self.numero_modulo}')
        return ' · '.join(partes)

    def __str__(self):
        return f'{self.get_tipo_adicional_display()} — {self.persona_nombre} (${self.valor})'


# ─────────────────────────────────────────────────────────
# Cierre de Curso — Historial archivado por ciclo
# ─────────────────────────────────────────────────────────
#
# Cuando un curso/jornada termina su ciclo (un mes, un trimestre, lo que el
# Gerente de Proyectos defina), se ejecuta un "Cierre de curso":
#   1. Se crea un CierreCurso (cabecera con totales y metadatos).
#   2. Se copian TODAS las matrículas y abonos asociados a `MatriculaArchivada`
#      y `AbonoArchivado` (snapshot completo, congelado para siempre).
#   3. Se borran las matrículas y abonos vivos para que la operación arranque
#      limpia el siguiente ciclo.
#
# Importante: el snapshot es **denormalizado**. Aunque guardamos FKs débiles
# (curso, jornada, estudiante) con on_delete=SET_NULL, también copiamos los
# textos legibles (nombre del curso, descripción de jornada, sede, etc.).
# Si más adelante se borra un curso o un estudiante, el historial sigue siendo
# legible al 100 %.

class CierreCurso(models.Model):
    """Cabecera de un cierre de curso/jornada. Es el registro padre del archivo."""

    ALCANCE = [
        ('jornada', 'Una jornada específica'),
        ('curso', 'Todo el curso (todas las jornadas)'),
        ('global', 'Cierre global (todos los cursos)'),
    ]

    # ── Identidad del cierre ──
    curso = models.ForeignKey(
        Curso, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cierres',
        help_text='Curso al que pertenece el cierre. Puede quedar nulo si el curso se elimina luego.'
    )
    curso_nombre = models.CharField(
        max_length=150,
        help_text='Nombre del curso al momento del cierre (denormalizado).'
    )
    curso_categoria = models.CharField(
        max_length=80, blank=True,
        help_text='Nombre de la categoría del curso al momento del cierre.'
    )
    jornada = models.ForeignKey(
        JornadaCurso, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cierres',
        help_text='Jornada cerrada (si el alcance es "jornada"). Nulo para cierre de curso entero.'
    )
    jornada_descripcion = models.CharField(
        max_length=250, blank=True,
        help_text='Descripción legible de la jornada al momento del cierre.'
    )
    jornada_modalidad = models.CharField(
        max_length=20, choices=MODALIDADES, blank=True,
        help_text='Modalidad de la jornada cerrada.'
    )
    jornada_fecha_inicio = models.DateField(null=True, blank=True)
    jornada_sede = models.CharField(max_length=100, blank=True)

    alcance = models.CharField(
        max_length=20, choices=ALCANCE, default='jornada'
    )

    # ── Etiqueta libre del ciclo (ej. "Mayo 2026", "Ciclo 2025-Q4") ──
    ciclo_etiqueta = models.CharField(
        max_length=80, blank=True,
        help_text='Etiqueta opcional para identificar el ciclo (ej. "Mayo 2026", "Trimestre I").'
    )
    observaciones = models.TextField(blank=True)

    # ── Totales congelados ──
    total_matriculas = models.PositiveIntegerField(default=0)
    total_facturado = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Suma de valor_neto (valor_curso - descuento) de todas las matrículas archivadas.'
    )
    total_cobrado = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Suma de valor_pagado de todas las matrículas archivadas.'
    )
    total_pendiente = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00')
    )
    conteo_pagado = models.PositiveIntegerField(default=0)
    conteo_parcial = models.PositiveIntegerField(default=0)
    conteo_pendiente = models.PositiveIntegerField(default=0)
    conteo_retiro = models.PositiveIntegerField(default=0)

    # ── Para cierres globales: la modalidad afectada (presencial/online/todas) ──
    modalidad_global = models.CharField(
        max_length=20, blank=True,
        help_text='Solo para alcance="global": presencial, online o "" (todas las modalidades).'
    )

    # ── ¿Se limpió también el directorio de estudiantes? ──
    limpio_directorio = models.BooleanField(
        default=False,
        help_text='True si en este cierre se borraron además los estudiantes huérfanos del directorio.'
    )
    total_estudiantes_archivados = models.PositiveIntegerField(default=0)

    # ── Auditoría ──
    fecha_cierre = models.DateTimeField(auto_now_add=True)
    cerrado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cierres_realizados',
        help_text='Usuario administrador que ejecutó el cierre.'
    )

    class Meta:
        verbose_name = 'Cierre de Curso'
        verbose_name_plural = 'Cierres de Curso'
        ordering = ['-fecha_cierre']

    def __str__(self):
        if self.jornada_descripcion:
            return f'{self.curso_nombre} — {self.jornada_descripcion} (cerrado {self.fecha_cierre:%d/%m/%Y})'
        return f'{self.curso_nombre} (cerrado {self.fecha_cierre:%d/%m/%Y})'

    @property
    def encabezado(self):
        partes = [self.curso_nombre]
        if self.jornada_descripcion:
            partes.append(self.jornada_descripcion)
        if self.ciclo_etiqueta:
            partes.append(f'[{self.ciclo_etiqueta}]')
        return ' · '.join(partes)


class MatriculaArchivada(models.Model):
    """
    Snapshot completo de una matrícula al momento del cierre.
    Todos los campos visibles de la lista de matrículas viven aquí
    como datos planos (denormalizados) para que el historial sea legible
    siempre, aunque luego se borren cursos o estudiantes.
    """

    cierre = models.ForeignKey(
        CierreCurso, on_delete=models.CASCADE, related_name='matriculas_archivadas'
    )

    # ── FK débiles (pueden quedar nulas si se eliminan los originales) ──
    matricula_original_id = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='ID de la matrícula original antes del cierre (auditoría).'
    )
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='matriculas_archivadas'
    )
    curso = models.ForeignKey(
        Curso, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='matriculas_archivadas'
    )
    jornada = models.ForeignKey(
        JornadaCurso, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='matriculas_archivadas'
    )

    # ── Datos del estudiante (denormalizados) ──
    cedula = models.CharField(max_length=20)
    apellidos = models.CharField(max_length=120)
    nombres = models.CharField(max_length=120)
    edad = models.CharField(max_length=10, blank=True)
    correo = models.EmailField(blank=True)
    celular = models.CharField(max_length=30, blank=True)
    ciudad_estudiante = models.CharField(max_length=80, blank=True)
    nivel_formacion = models.CharField(max_length=30, blank=True)
    talla_camiseta = models.CharField(max_length=4, blank=True)

    # ── Datos del curso/jornada (denormalizados) ──
    curso_nombre = models.CharField(max_length=150)
    curso_categoria = models.CharField(max_length=80, blank=True)
    jornada_descripcion = models.CharField(max_length=250, blank=True)
    jornada_fecha_inicio = models.DateField(null=True, blank=True)
    jornada_horario = models.CharField(max_length=50, blank=True)
    sede = models.CharField(max_length=100, blank=True)

    # ── Datos de la matrícula ──
    modalidad = models.CharField(max_length=20, choices=MODALIDADES)
    tipo_matricula = models.CharField(max_length=30, blank=True)
    estado = models.CharField(max_length=30, blank=True)
    fecha_matricula = models.DateField()
    valor_curso = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    valor_neto = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    valor_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    estado_pago = models.CharField(
        max_length=20,
        help_text='Pagado / Parcial / Pendiente / Retiro (congelado al cierre).'
    )

    # ── Datos del comprobante ──
    tipo_registro = models.CharField(max_length=30, blank=True)
    factura_realizada = models.CharField(max_length=2, blank=True)
    fact_nombres = models.CharField(max_length=120, blank=True)
    fact_apellidos = models.CharField(max_length=120, blank=True)
    fact_cedula = models.CharField(max_length=20, blank=True)
    fact_correo = models.EmailField(blank=True)
    link_comprobante = models.URLField(max_length=500, blank=True)

    observaciones = models.TextField(blank=True)

    # ── Auditoría ──
    registrado_por_nombre = models.CharField(
        max_length=120, blank=True,
        help_text='Nombre del asesor que registró la matrícula originalmente.'
    )
    creado_original = models.DateTimeField(
        null=True, blank=True,
        help_text='Fecha en que se creó la matrícula original.'
    )
    archivado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Matrícula archivada'
        verbose_name_plural = 'Matrículas archivadas'
        ordering = ['cierre', 'apellidos', 'nombres']
        indexes = [
            models.Index(fields=['cierre', 'estado_pago']),
            models.Index(fields=['cierre', 'modalidad']),
            models.Index(fields=['cedula']),
        ]

    @property
    def nombre_completo(self):
        return f'{self.apellidos} {self.nombres}'.strip()

    def __str__(self):
        return f'{self.nombre_completo} — {self.curso_nombre} (archivado)'


class AbonoArchivado(models.Model):
    """Snapshot completo de un abono al momento del cierre."""

    matricula_archivada = models.ForeignKey(
        MatriculaArchivada, on_delete=models.CASCADE, related_name='abonos_archivados'
    )
    cierre = models.ForeignKey(
        CierreCurso, on_delete=models.CASCADE, related_name='abonos_archivados'
    )

    # ── Datos del abono ──
    abono_original_id = models.PositiveIntegerField(null=True, blank=True)
    fecha = models.DateField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_pago = models.CharField(max_length=20, blank=True)
    tipo_pago_label = models.CharField(max_length=40, blank=True)
    numero_modulo = models.PositiveIntegerField(null=True, blank=True)
    cuenta_para_saldo = models.BooleanField(default=True)
    metodo = models.CharField(max_length=20, blank=True)
    metodo_label = models.CharField(max_length=40, blank=True)
    banco = models.CharField(max_length=30, blank=True)
    banco_label = models.CharField(max_length=40, blank=True)
    numero_recibo = models.CharField(max_length=30, blank=True)
    observaciones = models.TextField(blank=True)

    registrado_por_nombre = models.CharField(max_length=120, blank=True)
    creado_original = models.DateTimeField(null=True, blank=True)
    archivado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Abono archivado'
        verbose_name_plural = 'Abonos archivados'
        ordering = ['matricula_archivada', '-fecha']

    def __str__(self):
        return f'{self.numero_recibo or "—"} — ${self.monto} ({self.fecha})'


# ─────────────────────────────────────────────────────────
# Estudiante Archivado (directorio histórico)
# ─────────────────────────────────────────────────────────
#
# Al ejecutar un cierre con la opción "Limpiar directorio de estudiantes",
# los estudiantes cuyas matrículas se archivaron en ese cierre Y que NO
# tengan otras matrículas vivas en otros cursos, se copian aquí y se borran
# del directorio activo. El registro queda permanentemente consultable.

class EstudianteArchivado(models.Model):
    """Snapshot del estudiante (datos personales) al momento del cierre."""

    cierre = models.ForeignKey(
        CierreCurso, on_delete=models.CASCADE, related_name='estudiantes_archivados'
    )
    estudiante_original_id = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='ID del estudiante original (referencia auditiva).'
    )

    cedula = models.CharField(max_length=20)
    apellidos = models.CharField(max_length=100)
    nombres = models.CharField(max_length=100)
    edad = models.PositiveIntegerField(null=True, blank=True)
    correo = models.EmailField(blank=True)
    celular = models.CharField(max_length=20, blank=True)
    nivel_formacion = models.CharField(max_length=80, blank=True)
    titulo_profesional = models.CharField(max_length=200, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)

    creado_original = models.DateTimeField(
        null=True, blank=True,
        help_text='Fecha en que se registró originalmente el estudiante.'
    )
    archivado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Estudiante archivado'
        verbose_name_plural = 'Estudiantes archivados'
        ordering = ['-archivado_en', 'apellidos', 'nombres']
        indexes = [
            models.Index(fields=['cedula']),
            models.Index(fields=['cierre']),
        ]

    @property
    def nombre_completo(self):
        return f'{self.apellidos} {self.nombres}'.strip()

    def __str__(self):
        return f'{self.cedula} — {self.nombre_completo} (archivado)'


class AdicionalArchivado(models.Model):
    """Snapshot completo de un registro Adicional al momento del cierre."""

    cierre = models.ForeignKey(
        CierreCurso, on_delete=models.CASCADE, related_name='adicionales_archivados',
        null=True, blank=True,
        help_text='Cierre asociado (puede ser nulo si se archivó al limpiar directorio).'
    )
    adicional_original_id = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='ID del adicional original (referencia auditiva).'
    )

    # ── Datos del adicional ──
    tipo_adicional = models.CharField(max_length=30)
    tipo_adicional_label = models.CharField(max_length=50, blank=True)
    
    # ── Datos de la persona ──
    persona_nombre = models.CharField(max_length=200, blank=True)
    persona_cedula = models.CharField(max_length=20, blank=True)
    persona_celular = models.CharField(max_length=30, blank=True)
    origen_label = models.CharField(max_length=30, blank=True)

    # ── Curso / Detalle ──
    curso_nombre = models.CharField(max_length=150, blank=True)
    modalidad = models.CharField(max_length=20, blank=True)
    talla_camiseta = models.CharField(max_length=4, blank=True)
    numero_modulo = models.PositiveIntegerField(null=True, blank=True)

    # ── Pago ──
    fecha = models.DateField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, blank=True)
    metodo_pago_label = models.CharField(max_length=40, blank=True)
    banco = models.CharField(max_length=30, blank=True)
    banco_label = models.CharField(max_length=40, blank=True)
    numero_recibo = models.CharField(max_length=30, blank=True)

    # ── Factura ──────────────────────────────────────────
    factura_realizada = models.CharField(max_length=2, blank=True)
    fact_nombres = models.CharField(max_length=120, blank=True)
    fact_apellidos = models.CharField(max_length=120, blank=True)
    fact_cedula = models.CharField(max_length=20, blank=True)
    fact_correo = models.EmailField(blank=True)
    
    observaciones = models.TextField(blank=True)

    # ── Auditoría ──
    registrado_por_nombre = models.CharField(max_length=120, blank=True)
    creado_original = models.DateTimeField(null=True, blank=True)
    archivado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Adicional archivado'
        verbose_name_plural = 'Adicionales archivados'
        ordering = ['-archivado_en', '-fecha']
        indexes = [
            models.Index(fields=['persona_cedula']),
            models.Index(fields=['cierre']),
        ]

    def __str__(self):
        return f'{self.tipo_adicional_label} — {self.persona_nombre} (${self.valor}) (archivado)'


# ─────────────────────────────────────────────────────────
# Cierre Administrativo (cierre financiero del periodo)
# ─────────────────────────────────────────────────────────
#
# A diferencia del CierreCurso (que archiva matrículas), el CierreAdministrativo
# congela el ESTADO FINANCIERO de un periodo (normalmente un mes):
#   - Ingresos del periodo (abonos vivos + abonos archivados de cierres de curso
#     + ventas manuales + adicionales).
#   - Egresos del periodo.
#   - Balance neto.
#
# Es un snapshot contable. No borra nada (los egresos se conservan), solo
# fotografía los totales para tener un "corte de caja" oficial del mes que ya
# no cambia aunque después se hagan cierres de curso o se editen registros.

class CierreAdministrativo(models.Model):
    """Corte de caja / cierre financiero de un periodo (mes)."""

    # ── Periodo cubierto ──
    anio = models.PositiveIntegerField()
    mes = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Mes (1-12). Si es nulo, el cierre cubre todo el año.'
    )
    etiqueta = models.CharField(
        max_length=80, blank=True,
        help_text='Etiqueta libre (ej. "Corte Mayo 2026").'
    )
    fecha_desde = models.DateField()
    fecha_hasta = models.DateField()

    # ── Ingresos congelados (desglose) ──
    ingreso_abonos = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Abonos vivos del periodo.'
    )
    ingreso_abonos_archivados = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Abonos de cursos cerrados (archivados) del periodo.'
    )
    ingreso_ventas = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Ventas/comprobantes manuales del periodo.'
    )
    ingreso_adicionales = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Adicionales (certificados, supletorios, camisas) del periodo.'
    )
    ingreso_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00')
    )

    # ── Egresos congelados ──
    egreso_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00')
    )
    egresos_detalle_json = models.TextField(
        blank=True,
        help_text='JSON con el desglose de egresos por categoría al momento del cierre.'
    )

    # ── Balance ──
    balance_neto = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='ingreso_total - egreso_total.'
    )

    # ── Referencias a cierres de curso incluidos en este periodo ──
    cierres_curso_incluidos = models.PositiveIntegerField(
        default=0,
        help_text='Cuántos cierres de curso cayeron dentro de este periodo.'
    )
    monto_cierres_curso = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Total cobrado en los cierres de curso de este periodo.'
    )

    observaciones = models.TextField(blank=True)

    # ── Auditoría ──
    fecha_cierre = models.DateTimeField(auto_now_add=True)
    cerrado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cierres_admin_realizados'
    )

    class Meta:
        verbose_name = 'Cierre administrativo'
        verbose_name_plural = 'Cierres administrativos'
        ordering = ['-anio', '-mes', '-fecha_cierre']

    def __str__(self):
        return f'{self.encabezado} — balance ${self.balance_neto}'

    @property
    def encabezado(self):
        if self.etiqueta:
            return self.etiqueta
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        if self.mes:
            return f'Corte {meses[self.mes]} {self.anio}'
        return f'Corte anual {self.anio}'
