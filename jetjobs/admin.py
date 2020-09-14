from django.contrib import admin
from jetjobs.models import Advanced_Job
# Register your models here.


@admin.register(Advanced_Job)
class JobsAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'interval', 'rsi_period', 'rsi_value', 'bb_period', 'bb_std_num', 'bb_option')#'bb_upperband', 'bb_lowerband')
    # ordering = ['created']
    fieldsets = (
        (None, {
            'fields': ('name', 'symbol', 'interval', 'rsi_period', 'rsi_value', 'bb_period', 'bb_std_num', 'bb_option') # 'bb_upperband', 'bb_lowerband')
        }),
    )
