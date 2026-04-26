"""
Carga las 72 preguntas reales del PreTest SAQ desde pretest.xlsx.

Fuentes:
  pretest.xlsx   → 72 preguntas con SAQ asignado (fuente principal)
  aoc_por_imagen → Mapeo de correspondencia multi-SAQ (Part 2h)

Tipos de input por pregunta:
  Q1–Q62   → elegibilidad  (Sí / No / N/A / No probado)
  Q63      → texto_corto   (nombre del servicio evaluado)
  Q64      → checkbox_multi (tipo de servicio)
  Q65      → checkbox_multi (hosting provider)
  Q66      → checkbox_multi (managed services)
  Q67      → checkbox_multi (payment processing)
  Q68      → checkbox_multi (additional services)
  Q69      → texto_corto   (nombre servicio NO evaluado)
  Q70      → checkbox_multi (tipo NO evaluado)
  Q71      → checkbox_multi (categorías excluidas)
  Q72      → texto_largo   (motivo de exclusión)

Uso:
    python manage.py cargar_pretest
    python manage.py cargar_pretest --limpiar
"""

from django.core.management.base import BaseCommand
from saq.models import PreguntaSAQ

# ─────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE TIPOS DE INPUT
# ─────────────────────────────────────────────────────────────────

# Preguntas que NO son elegibilidad pura (el resto = elegibilidad)
TIPOS_ESPECIALES = {
    63: ('texto_corto',    None, 200),
    64: ('checkbox_multi', ['Hosting Provider', 'Managed Services', 'Payment Processing',
                            'Back office', 'Otro'], None),
    65: ('checkbox_multi', ['Aplicaciones/software', 'Hardware', 'Infraestructura/red',
                            'Espacio físico (co-location)', 'Almacenamiento',
                            'Servicios web-hosting', 'Seguridad', '3-D Secure Hosting',
                            'Multi-tenant', 'Otro'], None),
    66: ('checkbox_multi', ['Seguridad de sistemas', 'Soporte técnico IT',
                            'Seguridad física', 'Gestión de terminales POI',
                            'Otro servicio gestionado'], None),
    67: ('checkbox_multi', ['Punto de interacción POI / card-present',
                            'Internet / e-commerce', 'MOTO / Call Center',
                            'Cajeros ATM', 'Otro procesamiento de pagos'], None),
    68: ('checkbox_multi', ['Gestión de cuentas', 'Servicios back-office',
                            'Facturación', 'Liquidación', 'Proveedor de red',
                            'Prevención de fraude', 'Pasarela de pagos',
                            'Servicios prepagados', 'Gestión de registros',
                            'Pagos de impuestos/gobierno', 'Otro'], None),
    69: ('texto_corto',    None, 200),
    70: ('checkbox_multi', ['Hosting Provider', 'Managed Services', 'Payment Processing',
                            'Otro'], None),
    71: ('checkbox_multi', ['Hosting Provider', 'Managed Services', 'Payment Processing',
                            'Otros servicios'], None),
    72: ('texto_largo',    None, 500),
}

# ─────────────────────────────────────────────────────────────────
# CORRESPONDENCIA MULTI-SAQ (extraída de aoc_por_imagen.xlsx Part 2h)
# Cuando una pregunta de pretest.xlsx (SAQ primario) también corresponde
# a otros SAQs según el AOC, se listan aquí los extras.
# ─────────────────────────────────────────────────────────────────

# {numero_pregunta: [saq_extra1, saq_extra2, ...]}
MULTISAQ_EXTRA = {
    # SAQ A — preguntas que también aplican a AEP y B
    1:  ['AEP', 'B'],
    2:  ['AEP', 'B'],
    3:  ['AEP', 'B'],
    4:  ['AEP', 'B'],
    5:  ['AEP', 'B'],
    6:  ['AEP', 'B'],
    7:  ['AEP', 'B', 'BIP', 'C', 'CTV'],   # "datos solo en papel" aplica a todos
    # AEP — exclusivas (8-12) sin extra por AOC
    # B   — exclusivas (13-22) sin extra
    # BIP — exclusivas (23-34) sin extra
    # C   — exclusivas (35-40) sin extra
    # CTV — exclusivas (41-49) sin extra
    # D-COMERCIO y D-PROVEEDOR — sin superposición
}

# ─────────────────────────────────────────────────────────────────
# LAS 72 PREGUNTAS  (extraídas directamente de pretest.xlsx)
# Formato: (numero, saq_primario, pregunta_es, pregunta_en)
# ─────────────────────────────────────────────────────────────────

PREGUNTAS = [
    # ── SAQ A ──────────────────────────────────────────────────────────
    (1,  'A', '¿Tiene externalizado el servicio de manejo de los datos de tarjeta con un proveedor de servicios externo, ya sea para pagos, reservas o almacenamiento de datos de tarjetas?', 'Have you outsourced card data handling to an external service provider, whether for payments, reservations, or card data storage?'),
    (2,  'A', '¿Su página web permite realizar pagos mediante un iframe o redirección a una página proporcionada por su banco u otro proveedor certificado PCI DSS?', 'Does your website allow payments via an iframe or redirection to a page provided by your bank or another PCI DSS-certified provider?'),
    (3,  'A', '¿El comerciante acepta únicamente transacciones sin presencia física de la tarjeta (comercio electrónico o pedidos por correo/teléfono)?', 'Does the merchant only accept transactions without the physical presence of the card (e-commerce or mail/telephone orders)?'),
    (4,  'A', '¿Todo el procesamiento de datos de cuentas está completamente externalizado a un proveedor de servicios externo (TPSP) o procesador de pagos que cumple con la norma PCI DSS?', 'Is all account data processing completely outsourced to an external service provider (TPSP) or payment processor that complies with the PCI DSS standard?'),
    (5,  'A', '¿El comerciante ha confirmado que los TPSP utilizados cumplen con la norma PCI DSS?', 'Has the merchant confirmed that the TPSPs used comply with the PCI DSS standard?'),
    (6,  'A', '¿Todos los elementos de las páginas o formularios de pago que se muestran al cliente provienen únicamente de un TPSP o procesador de pagos certificado PCI DSS?', 'Do all elements of the payment pages or forms displayed to the customer come solely from a PCI DSS-certified TPSP or payment processor?'),
    (7,  'A', '¿El comerciante conserva algún dato de cuenta en papel (por ejemplo, informes impresos o recibos), sin recibirlos electrónicamente?', 'Does the merchant retain any account data on paper (e.g., printed reports or receipts), rather than receiving it electronically?'),
    # ── SAQ AEP ─────────────────────────────────────────────────────────
    (8,  'AEP', '¿Su página web permite realizar pagos utilizando mecanismos como API, JavaScript o Direct Post, proporcionados por un proveedor de servicios externo certificado PCI DSS?', 'Does your website allow payments using mechanisms such as API, JavaScript, or Direct Post, provided by a PCI DSS-certified external service provider?'),
    (9,  'AEP', '¿El comerciante acepta únicamente transacciones sin presencia física de la tarjeta (comercio electrónico o pedidos por correo/teléfono)?', 'Does the merchant only accept transactions without the physical presence of the card (e-commerce or mail/telephone orders)?'),
    (10, 'AEP', '¿Todo el procesamiento de los datos de las cuentas está completamente externalizado a un proveedor de servicios externo (TPSP) o procesador de pagos que cumple con la norma PCI DSS?', 'Is all account data processing completely outsourced to a third-party service provider (TPSP) or payment processor that complies with PCI DSS?'),
    (11, 'AEP', '¿El comerciante ha confirmado que los TPSP utilizados cumplen con la norma PCI DSS?', 'Has the merchant confirmed that the TPSPs used comply with PCI DSS?'),
    (12, 'AEP', '¿El comerciante conserva algún dato de cuenta únicamente en papel (por ejemplo, informes impresos o recibos), sin recibirlos electrónicamente?', 'Does the merchant retain any account data solely in paper form (e.g., printed reports or receipts), without receiving it electronically?'),
    # ── SAQ B ───────────────────────────────────────────────────────────
    (13, 'B',   '¿Manejan sus empleados TPVs o datáfonos conectados a una red móvil 3G/4G de una operadora de telecomunicaciones?', 'Do your employees use POS terminals or card readers connected to a 3G/4G mobile network provided by a telecommunications operator?'),
    (14, 'B',   '¿Utilizan terminales de pago independientes sin conexión a internet?', 'Do you use standalone payment terminals without an internet connection?'),
    (15, 'B',   '¿Existe una política que prohíba el almacenamiento electrónico de datos del titular de la tarjeta?', 'Is there a policy prohibiting the electronic storage of cardholder data?'),
    (16, 'B',   '¿Se aplican restricciones de acceso físico a los dispositivos de pago?', 'Are physical access restrictions applied to payment devices?'),
    (17, 'B',   '¿Se realiza una inspección regular de los terminales de pago para detectar manipulaciones o anomalías?', 'Are payment terminals regularly inspected for tampering or anomalies?'),
    (18, 'B',   '¿El comerciante acepta únicamente transacciones sin presencia física de la tarjeta (comercio electrónico o pedidos por correo/teléfono)?', 'Does the merchant only accept transactions without the physical presence of the card (e-commerce or mail/telephone orders)?'),
    (19, 'B',   '¿Todo el procesamiento de los datos de las cuentas está completamente externalizado a un proveedor de servicios externo (TPSP) o procesador de pagos que cumple con la norma PCI DSS?', 'Is all account data processing completely outsourced to a third-party service provider (TPSP) or payment processor that complies with the PCI DSS standard?'),
    (20, 'B',   '¿El comerciante ha confirmado que los TPSP utilizados cumplen con la norma PCI DSS?', 'Has the merchant confirmed that the TPSPs used comply with the PCI DSS standard?'),
    (21, 'B',   '¿El comerciante no almacena, procesa ni transmite electrónicamente ningún dato de la cuenta en sus sistemas o instalaciones, confiando completamente en un TPSP?', 'Does the merchant not store, process, or electronically transmit any account data on its systems or premises, relying entirely on a TPSP?'),
    (22, 'B',   '¿El comerciante conserva únicamente datos de cuenta en papel (por ejemplo, informes impresos o recibos), sin recibirlos electrónicamente?', 'Does the merchant only retain account data on paper (e.g., printed reports or receipts), without receiving it electronically?'),
    # ── SAQ BIP ─────────────────────────────────────────────────────────
    (23, 'BIP', '¿Manejan sus empleados TPVs o datáfonos conectados a su red interna (ya sea por WiFi o por cable)?', 'Do your employees use POS terminals or card readers connected to your internal network (either via WiFi or cable)?'),
    (24, 'BIP', '¿Los terminales de pago cuentan con conexión IP aislada del resto de la red del comerciante?', 'Do the payment terminals have an IP connection that is isolated from the rest of the merchant\'s network?'),
    (25, 'BIP', '¿Se han configurado firewalls y segmentación de red para proteger los terminales de pago?', 'Have firewalls and network segmentation been configured to protect the payment terminals?'),
    (26, 'BIP', '¿Existen controles de autenticación para el acceso remoto a los sistemas relacionados con pagos?', 'Are there authentication controls for remote access to payment-related systems?'),
    (27, 'BIP', '¿Se aplican parches de seguridad regularmente en los terminales de pago?', 'Are security patches applied regularly to payment terminals?'),
    (28, 'BIP', '¿El comerciante utiliza únicamente dispositivos PTS POI independientes, homologados por PCI (excluidos SCR y SCRP), conectados por IP al procesador de pagos?', 'Does the merchant only use PCI-approved standalone PTS POI devices (excluding SCR and SCRP) connected via IP to the payment processor?'),
    (29, 'BIP', '¿Los dispositivos POI utilizados están validados por el programa PTS POI según el sitio web de PCI SSC?', 'Are the POI devices used validated by the PTS POI program according to the PCI SSC website?'),
    (30, 'BIP', '¿Los dispositivos PTS POI conectados por IP están completamente aislados de otros sistemas del entorno del comerciante mediante segmentación de red?', 'Are IP-connected PTS POI devices completely isolated from other systems in the merchant\'s environment through network segmentation?'),
    (31, 'BIP', '¿La única transmisión de datos de cuenta se realiza desde los dispositivos PTS POI aprobados al procesador de pagos?', 'Is the only transmission of account data from approved PTS POI devices to the payment processor?'),
    (32, 'BIP', '¿Los dispositivos PTS POI no dependen de ningún otro dispositivo (como ordenadores, móviles o tabletas) para conectarse al procesador de pagos?', 'Do PTS POI devices not rely on any other devices (such as computers, mobile phones, or tablets) to connect to the payment processor?'),
    (33, 'BIP', '¿El comerciante evita almacenar datos de cuentas en formato electrónico?', 'Does the merchant avoid storing account data in electronic format?'),
    (34, 'BIP', '¿Los datos de cuenta que el comerciante pueda conservar están únicamente en papel (por ejemplo, informes impresos o recibos), y no se reciben electrónicamente?', 'Is any account data that the merchant may retain only in paper form (e.g., printed reports or receipts), and not received electronically?'),
    # ── SAQ C ───────────────────────────────────────────────────────────
    (35, 'C',   '¿Su comercio dispone de aplicaciones con sistemas de pagos que se conectan por internet?', 'Does your business have applications with payment systems that connect to the internet?'),
    (36, 'C',   '¿Los terminales de pago están conectados a internet pero no tienen conexión con otros sistemas internos?', 'Are the payment terminals connected to the internet but not connected to other internal systems?'),
    (37, 'C',   '¿El sistema de solicitud de pago no está conectado a ningún otro sistema dentro del entorno del comerciante?', 'Is the payment request system not connected to any other system within the merchant\'s environment?'),
    (38, 'C',   '¿La ubicación física del entorno del punto de venta no está conectada a otras instalaciones o ubicaciones, y cualquier LAN es exclusiva de una sola ubicación?', 'Is the physical location of the point of sale environment not connected to other facilities or locations, and is any LAN exclusive to a single location?'),
    (39, 'C',   '¿El comerciante tiene un sistema de aplicación de pagos y una conexión a Internet en el mismo dispositivo y/o red local (LAN)?', 'Does the merchant have a payment application system and an internet connection on the same device and/or local area network (LAN)?'),
    (40, 'C',   '¿El comerciante conserva datos de cuenta únicamente en papel (por ejemplo, informes impresos o recibos), sin recibirlos electrónicamente?', 'Does the merchant retain account data solely in paper form (e.g., printed reports or receipts), without receiving it electronically?'),
    # ── SAQ CTV ─────────────────────────────────────────────────────────
    (41, 'CTV', '¿Sus empleados introducen manualmente los datos de tarjeta en una aplicación de un tercero?', 'Do your employees manually enter card details into a third-party application?'),
    (42, 'CTV', '¿El ingreso manual de datos se realiza exclusivamente a través de un terminal de pago virtual?', 'Is manual data entry performed exclusively through a virtual payment terminal?'),
    (43, 'CTV', '¿Las estaciones de trabajo utilizadas para pagos están dedicadas exclusivamente a esa función?', 'Are the workstations used for payments dedicated exclusively to that function?'),
    (44, 'CTV', '¿El único procesamiento de pagos se realiza mediante un terminal de pago virtual accesible desde un navegador web conectado a Internet?', 'Is the only payment processing performed through a virtual payment terminal accessible from a web browser connected to the Internet?'),
    (45, 'CTV', '¿La solución de terminal de pago virtual es proporcionada y alojada por un proveedor de servicios externo validado por PCI DSS?', 'Is the virtual payment terminal solution provided and hosted by a PCI DSS-validated third-party service provider?'),
    (46, 'CTV', '¿Solo se puede acceder a la solución de terminal de pago virtual desde un dispositivo informático aislado, ubicado en una única ubicación y segmentado de otros sistemas del comerciante?', 'Is the virtual payment terminal solution only accessible from an isolated computer device, located in a single location and segmented from other merchant systems?'),
    (47, 'CTV', '¿El dispositivo informático utilizado para acceder al terminal de pago virtual no tiene instalado ningún software que almacene datos de cuentas?', 'Does the computing device used to access the virtual payment terminal have no software installed that stores account data?'),
    (48, 'CTV', '¿El dispositivo informático no tiene conectados dispositivos de hardware que puedan capturar o almacenar datos de cuentas (por ejemplo, lectores de tarjetas)?', 'Does the computing device have no hardware devices connected to it that can capture or store account data (e.g., card readers)?'),
    (49, 'CTV', '¿El comerciante no recibe, transmite ni almacena datos de cuentas electrónicamente a través de ningún canal (como redes internas o Internet)?', 'Does the merchant not receive, transmit, or store account data electronically through any channel (such as internal networks or the Internet)?'),
    # ── SAQ D-COMERCIO ──────────────────────────────────────────────────
    (50, 'D-COMERCIO', '¿El comerciante almacena datos de tarjetas en algún sistema informático dentro de su entorno?', 'Does the merchant store card data on any computer system within its environment?'),
    (51, 'D-COMERCIO', '¿El comerciante realiza almacenamiento electrónico de datos del titular de la tarjeta (por ejemplo, PAN, fecha de vencimiento, etc.)?', 'Does the merchant electronically store cardholder data (e.g., PAN, expiration date, etc.)?'),
    (52, 'D-COMERCIO', '¿Se realiza una revisión diaria de los registros de seguridad relacionados con el entorno de datos de tarjetas (CDE)?', 'Is there a daily review of security logs related to the card data environment (CDE)?'),
    (53, 'D-COMERCIO', '¿El comerciante ha realizado una evaluación de riesgos específica sobre el manejo de datos de tarjetas?', 'Has the merchant conducted a specific risk assessment on card data handling?'),
    (54, 'D-COMERCIO', '¿El comerciante cumple con todos los requisitos aplicables de la norma PCI DSS?', 'Does the merchant comply with all applicable PCI DSS requirements?'),
    (55, 'D-COMERCIO', '¿El comerciante tiene relaciones con proveedores de servicios externos que almacenan, procesan o transmiten datos de cuentas en su nombre (por ejemplo, pasarelas de pago, PSP, procesadores de pagos)?', 'Does the merchant have relationships with external service providers that store, process, or transmit account data on its behalf (e.g., payment gateways, PSPs, payment processors)?'),
    (56, 'D-COMERCIO', '¿Alguno de los proveedores externos gestiona componentes del sistema incluidos en el alcance de la evaluación PCI DSS (por ejemplo, servicios de seguridad de red, antimalware, SIEM, servicios de nube como IaaS, PaaS, SaaS)?', 'Do any of the external providers manage system components included in the scope of the PCI DSS assessment (e.g., network security services, antimalware, SIEM, cloud services such as IaaS, PaaS, SaaS)?'),
    (57, 'D-COMERCIO', '¿Alguno de los proveedores externos podría afectar la seguridad del entorno de datos de tarjetas (CDE), por ejemplo, mediante acceso remoto o desarrollo de software a medida?', 'Could any of the external providers affect the security of the card data environment (CDE), for example through remote access or custom software development?'),
    # ── SAQ D-PROVEEDOR ─────────────────────────────────────────────────
    (58, 'D-PROVEEDOR', '¿El proveedor de servicios maneja datos de tarjetas en nombre de terceros?', 'Does the service provider handle card data on behalf of third parties?'),
    (59, 'D-PROVEEDOR', '¿Se realiza una revisión de privilegios de acceso cada tres meses en los sistemas que procesan o protegen datos de tarjetas?', 'Is an access privilege review conducted every three months on systems that process or protect card data?'),
    (60, 'D-PROVEEDOR', '¿Están configuradas alertas para detectar fallos en los mecanismos de seguridad que protegen el entorno de datos de tarjetas (CDE)?', 'Are alerts configured to detect failures in the security mechanisms that protect the card data environment (CDE)?'),
    (61, 'D-PROVEEDOR', '¿Se ha realizado una evaluación de riesgos específica para los servicios prestados relacionados con el procesamiento, almacenamiento o transmisión de datos de tarjetas?', 'Has a specific risk assessment been performed for services related to the processing, storage, or transmission of card data?'),
    (62, 'D-PROVEEDOR', '¿Se realiza una revisión anual del uso de TLS y otros mecanismos de criptografía en los sistemas que manejan datos de tarjetas?', 'Is an annual review of TLS and other cryptographic mechanisms performed on systems that handle card data?'),
    (63, 'D-PROVEEDOR', '¿Cuál es el nombre del servicio o los servicios que fueron evaluados en esta revisión PCI DSS?', 'What is the name of the service(s) that were evaluated in this PCI DSS review?'),
    (64, 'D-PROVEEDOR', '¿Qué tipo de servicio(s) se evaluaron? (Puedes seleccionar más de uno si aplica)', 'What type of service(s) were evaluated? (You can select more than one if applicable)'),
    (65, 'D-PROVEEDOR', '¿El servicio evaluado incluye alguno de los siguientes elementos como proveedor de hosting?', 'Does the evaluated service include any of the following elements as a hosting provider?'),
    (66, 'D-PROVEEDOR', '¿El servicio evaluado incluye alguno de los siguientes como servicios gestionados?', 'Does the service being evaluated include any of the following as managed services?'),
    (67, 'D-PROVEEDOR', '¿El servicio evaluado incluye alguno de los siguientes tipos de procesamiento de pagos?', 'Does the service being evaluated include any of the following types of payment processing?'),
    (68, 'D-PROVEEDOR', '¿El servicio evaluado incluye alguno de los siguientes servicios adicionales?', 'Does the service being evaluated include any of the following additional services?'),
    (69, 'D-PROVEEDOR', '¿Cuál es el nombre del servicio o los servicios que no fueron evaluados en esta revisión PCI DSS?', 'What is the name of the service(s) that were not evaluated in this PCI DSS review?'),
    (70, 'D-PROVEEDOR', '¿Qué tipo de servicio(s) no fueron evaluados?', 'What type of service(s) were not evaluated?'),
    (71, 'D-PROVEEDOR', '¿Alguno de los servicios excluidos pertenece a las siguientes categorías?', 'Do any of the excluded services fall into the following categories?'),
    (72, 'D-PROVEEDOR', '¿Por qué estos servicios no fueron incluidos en el alcance de la evaluación?', 'Why were these services not included in the scope of the evaluation?'),
]


class Command(BaseCommand):
    help = 'Carga las 72 preguntas reales del PreTest SAQ (fuente: pretest.xlsx + aoc_por_imagen.xlsx)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Elimina TODAS las preguntas existentes antes de insertar',
        )

    def handle(self, *args, **options):
        if options['limpiar']:
            n, _ = PreguntaSAQ.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'  {n} preguntas eliminadas.\n'))

        creadas = actualizadas = 0

        for num, saq, es, en in PREGUNTAS:
            # Determinar tipo de input
            if num in TIPOS_ESPECIALES:
                tipo_input, opciones, max_chars = TIPOS_ESPECIALES[num]
            else:
                tipo_input, opciones, max_chars = 'elegibilidad', None, None

            # SAQs extra (multi-SAQ)
            extras = ','.join(MULTISAQ_EXTRA.get(num, []))

            # Sección AOC
            if num <= 62:
                if saq == 'D-PROVEEDOR':
                    seccion = 'Part 2h. Eligibility (D-Proveedor)'
                else:
                    seccion = 'Part 2h. Eligibility to Complete SAQ'
            else:
                seccion = 'Part 2a. Scope Verification (D-Proveedor)'

            obj, created = PreguntaSAQ.objects.update_or_create(
                numero=num,
                defaults={
                    'tipo_saq':        saq,
                    'tipos_saq_extra': extras,
                    'tipo_input':      tipo_input,
                    'seccion_aoc':     seccion,
                    'pregunta_es':     es,
                    'pregunta_en':     en,
                    'opciones_json':   opciones,
                    'max_chars':       max_chars,
                    'version_pci':     '4.0.1',
                    'activo':          True,
                }
            )
            if created:
                creadas += 1
            else:
                actualizadas += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Carga completa:\n'
            f'  {creadas} creadas | {actualizadas} actualizadas\n'
            f'  Total: {PreguntaSAQ.objects.count()} preguntas\n'
        ))

        self.stdout.write('\nDistribución por SAQ:')
        for saq in ['A', 'AEP', 'B', 'BIP', 'C', 'CTV', 'D-COMERCIO', 'D-PROVEEDOR']:
            n = PreguntaSAQ.objects.filter(tipo_saq=saq).count()
            self.stdout.write(f'  SAQ {saq:12s} → {n} preguntas')

        self.stdout.write('\nDistribución por tipo de input:')
        for ti, label in [('elegibilidad', 'Elegibilidad'), ('checkbox_multi', 'Checkbox multi'),
                          ('texto_corto', 'Texto corto'), ('texto_largo', 'Texto largo')]:
            n = PreguntaSAQ.objects.filter(tipo_input=ti).count()
            if n:
                self.stdout.write(f'  {label:20s} → {n} preguntas')