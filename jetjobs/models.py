from django.db import models

# Create your models here.

class Advanced_Job(models.Model):

    user_id = models.CharField(verbose_name='User ID', max_length=30)
    symbol = models.CharField(verbose_name='symbol', max_length=30)
    name = models.CharField(verbose_name='Job Name', max_length=100)
    interval = models.CharField(max_length=30)
    rsi_period = models.IntegerField()
    rsi_value = models.DecimalField(max_digits=20, decimal_places=10)
    bb_period = models.IntegerField()
    bb_std_num = models.IntegerField()
    bb_option = models.CharField(max_length=100)
    
    # bb_upperband = models.DecimalField(max_digits=20, decimal_places=10)
    # bb_lowerband = models.DecimalField(max_digits=20, decimal_places=10)

    def __str__(self):
        return self.name
