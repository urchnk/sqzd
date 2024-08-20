from django.contrib import admin

from apps.roles.models import Provider, User


class UserAdmin(admin.ModelAdmin):
    pass


class ProviderAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)
admin.site.register(Provider, ProviderAdmin)
