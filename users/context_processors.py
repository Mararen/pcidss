from .models import ConfiguracionGeneral

def config_global(request):
    try:
        config = ConfiguracionGeneral.objects.get(id=1)
    except ConfiguracionGeneral.DoesNotExist:
        config = None
    return {"config_global": config}