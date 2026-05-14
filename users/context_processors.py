def config_global(request):
    try:
        config = ConfiguracionGeneral.objects.get(id=1)
    except Exception:
        config = None
    return {'config_global': config}