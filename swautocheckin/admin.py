from django.contrib import admin

from swautocheckin.models import Reservation, Passenger


class ReservationAdmin(admin.ModelAdmin):
    # fields = ['passenger', 'success', 'boarding_position']
    list_display = ('passenger', 'confirmation_num', 'flight_date', 'flight_time', 'success', 'boarding_position')

admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Passenger)