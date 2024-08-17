from django.contrib import admin

from apps.scheduler.models import Break, Reservation, Vacation


class ReservationAdmin(admin.ModelAdmin):
    pass


class VacationAdmin(admin.ModelAdmin):
    pass


class BreakAdmin(admin.ModelAdmin):
    pass


admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Vacation, VacationAdmin)
admin.site.register(Break, BreakAdmin)
