from django.apps import AppConfig

class TcmsUiCustomConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tcms_ui_custom'
    verbose_name = 'TCMS Custom UI'

    def ready(self):
        import tcms_ui_custom.signals
