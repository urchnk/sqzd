from django.contrib import admin

from apps.texts.models import Text


class TextAdmin(admin.ModelAdmin):
    pass


admin.site.register(Text, TextAdmin)
