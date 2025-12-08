from .models import SystemSettings

def system_settings_context(request):
    settings = SystemSettings.get_settings()
    return {'system_settings': settings}
