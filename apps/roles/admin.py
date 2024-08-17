from django.contrib import admin

from apps.roles.models import Company, Office, Provider, User


class UserAdmin(admin.ModelAdmin):
    pass


class ProviderAdmin(admin.ModelAdmin):
    pass


class CompanyAdmin(admin.ModelAdmin):
    pass


class OfficeAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)
admin.site.register(Provider, ProviderAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Office, OfficeAdmin)
