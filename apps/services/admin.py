from django.contrib import admin

from apps.services.models import Service, ServiceGroup


class ServiceAdmin(admin.ModelAdmin):
    pass


class ServiceGroupAdmin(admin.ModelAdmin):
    pass


admin.site.register(Service, ServiceAdmin)
admin.site.register(ServiceGroup, ServiceGroupAdmin)
