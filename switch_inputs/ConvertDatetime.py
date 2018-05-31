import pytz
import datetime

##
# \brief ConvertDatetime utility; useful to convert datetimes between different timezones.
class ConvertDatetime:
    ##
    # A class to convert datetimes between different zones using pytz and Python datetimes.
    #
    
    def __init__ (self, tz, year, month, day, hour, minute):
        ##
        # Class constructor.
        # \param self Object pointer.
        # \param tz Timezone.
        # \param year Year.
        # \param month Month.
        # \param day Day.
        # \param hour Hour.
        # \param minute Minute.
        self._datetime = datetime.datetime(year, month, day, hour, minute)
        self.tz = tz
        self._tz = pytz.timezone(ConvertDatetime._tz_string(tz))
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute

    def __str__ (self):
        ##
        # Print the datetime.
        # \param self Object pointer.
        return str(self._datetime)

    def _tz_string (gmt_tz):
        ##
        # Helper function to convert a simple timezone to a pytz one.
        # \param gmt_tz Timezone.
        return "Etc/GMT" + str(gmt_tz)

    def ConvertTo (self, gmt_tz):
        ##
        # Convert to the desiring timezone (uses Greenwich Time).
        # \param self Object pointer.
        # \param gmt_tz Timezone to convert to.
        self._datetime = pytz.timezone(ConvertDatetime._tz_string(gmt_tz)).localize(
            datetime.datetime(
                self.year,
                self.month,
                self.day,
                self.hour,
                self.minute)).astimezone(self._tz)
        self.tz = gmt_tz
        self._tz = pytz.timezone(ConvertDatetime._tz_string(gmt_tz))
        ConvertDatetime._update(self)

    def _update (self):
        ##
        # Update object information after changing the timezone.
        # \param self Object pointer.
        self.year = self._datetime.year
        self.month = self._datetime.month
        self.day = self._datetime.day
        self.hour = self._datetime.hour
        self.minute = self._datetime.minute
