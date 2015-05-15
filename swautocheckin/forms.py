from django import forms
from swautocheckin import checkin
from swautocheckin.checkin import RESPONSE_STATUS_INVALID, RESPONSE_STATUS_RES_NOT_FOUND, \
    RESPONSE_STATUS_SUCCESS, \
    RESPONSE_STATUS_TOO_EARLY, RESPONSE_STATUS_INVALID_PASSENGER_NAME


class EmailForm(forms.Form):
    email = forms.EmailField()
    email.widget.attrs['class'] = 'form-control input-lg'
    email.widget.attrs['placeholder'] = 'Enter your email to get started'


class ReservationForm(forms.Form):
    email = forms.CharField()
    email.widget.attrs['class'] = 'form-control input-lg'
    email.widget.attrs['readonly'] = True

    first_name = forms.CharField(max_length=30)
    first_name.widget.attrs['class'] = 'form-control input-lg'
    first_name.label = 'First Name'

    last_name = forms.CharField(max_length=30)
    last_name.widget.attrs['class'] = 'form-control input-lg'
    last_name.label = 'Last Name'

    confirmation_num = forms.CharField(max_length=13)
    confirmation_num.widget.attrs['class'] = 'form-control input-lg'
    confirmation_num.label = 'Confirmation Code'

    flight_date = forms.DateField()
    flight_date.widget.attrs['class'] = 'form-control input-lg'
    flight_date.widget.attrs['placeholder'] = 'Ex. 01/23/2014'
    flight_date.label = 'Flight Date'
    flight_date.input_formats = ['%m/%d/%Y']

    flight_time = forms.TimeField()
    flight_time.widget.attrs['placeholder'] = 'Ex. 7:30 pm (Pacific Standard Time)'
    flight_time.help_text = "Pacific Standard Time"
    flight_time.widget.attrs['class'] = 'form-control input-lg'
    flight_time.label = 'Flight Time'
    flight_time.input_formats = ['%H:%M', '%I:%M%p', '%I:%M %p']

    return_flight_date = forms.DateField()
    return_flight_date.required = False
    return_flight_date.widget.attrs['class'] = 'form-control input-lg'
    return_flight_date.widget.attrs['placeholder'] = 'Optional'
    return_flight_date.label = 'Return Flight Date'
    return_flight_date.input_formats = ['%m/%d/%Y']

    return_flight_time = forms.TimeField()
    return_flight_time.required = False
    return_flight_time.widget.attrs['placeholder'] = 'Optional'
    return_flight_time.help_text = "Pacific Standard Time"
    return_flight_time.widget.attrs['class'] = 'form-control input-lg'
    return_flight_time.label = 'Return Flight Time'
    return_flight_time.input_formats = ['%H:%M', '%I:%M%p', '%I:%M %p']

    def __init__(self, *args, **kwargs):
        super(ReservationForm, self).__init__(*args, **kwargs)
        if self.data.get('last_name') or (kwargs.get("initial") and kwargs.get("initial").get("last_name")):
            self.fields['last_name'].widget.attrs['readonly'] = True
        if self.data.get('first_name') or (kwargs.get("initial") and kwargs.get("initial").get("first_name")):
            self.fields['first_name'].widget.attrs['readonly'] = True

    class Meta:
        fieldsets = (
            ('Passenger Information', {
                'fields': ('first_name', 'last_name')
            }),

            ('Flight Information', {
                'fields': ('confirmation_num', 'flight_date', 'flight_time')
            }),

            ('Return Flight Information', {
                'fields': ('return_flight_date', 'return_flight_time')
            }),
        )

    def clean(self):
        cleaned_data = super(ReservationForm, self).clean()
        email = cleaned_data.get("email")
        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")
        conf_num = cleaned_data.get("confirmation_num")

        return_flight_time = cleaned_data.get("return_flight_time")
        return_flight_date = cleaned_data.get("return_flight_date")
        if return_flight_time and not return_flight_date:
            msg = u"Required with return flight time."
            self._errors["return_flight_date"] = self.error_class([msg])
            del cleaned_data["return_flight_date"]

        if return_flight_date and not return_flight_time:
            msg = u"Required with return flight date."
            self._errors["return_flight_time"] = self.error_class([msg])
            del cleaned_data["return_flight_time"]

        if first_name and last_name and conf_num:
            response_code, boarding_position = checkin.attempt_checkin(conf_num, first_name, last_name, email, do_checkin=False)
            if response_code is RESPONSE_STATUS_INVALID.code:
                msg = u"Invalid confirmation code."
                self._errors["confirmation_num"] = self.error_class([msg])
                del cleaned_data["confirmation_num"]
            elif response_code is RESPONSE_STATUS_RES_NOT_FOUND.code:
                raise forms.ValidationError("Reservation not found.")
            elif response_code is RESPONSE_STATUS_INVALID_PASSENGER_NAME.code:
                raise forms.ValidationError("Passenger name does not match confirmation code.")
            elif response_code is RESPONSE_STATUS_SUCCESS.code:
                pass  # todo handle successful checkin
            elif response_code is RESPONSE_STATUS_TOO_EARLY.code:
                pass
            else:
                raise forms.ValidationError("Error while looking up reservation.")

        # Always return the full collection of cleaned data.
        return cleaned_data