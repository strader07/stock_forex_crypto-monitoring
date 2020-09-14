from jet.dashboard.modules import DashboardModule
from jetjobs.models import Advanced_Job
from django import forms
from django.template.loader import render_to_string


class JobRecent(DashboardModule):
    template = 'dashboard_modules/provider.html'
    limit = 2
    column = 0
    ajax_load = True
    draggable = True

    def init_with_context(self, context):
        self.children = Advanced_Job.objects.all()


class JobSettingsForm(forms.Form):
    # print('setting')
    layout = forms.ChoiceField(label='Layout', choices=(('stacked', 'Stacked'), ('inline', 'Inline')))


class JobItemForm(forms.Form):
    # print('forms')
    title = forms.CharField(label='Job title')
    symbol = forms.CharField(label='Symbol')
    # interval = forms.CharField(label='interval')
    CHOICES = (
        ('1 min', '1 min'),
        ('2 min', '2 min'),
        ('5 min', '5 min'),
        ('15 min', '15 min'),
        ('30 min', '30 min'),
        ('60 min', '60 min'),
        ('90 min', '90 min'),
        ('1 hour', '1 hour'),
        ('5 hour', '5 hour'),
        ('5 day', '5 day'),
        ('1 week', '1 week'),
        ('1 month', '1 month'),
        ('3 month', '3 month'),)
    interval = forms.ChoiceField(choices=CHOICES, widget=forms.Select(), initial='5 min')
    rsi_period = forms.IntegerField(label='RSI period')
    rsi_value = forms.FloatField(label='RSI value')
    bb_period = forms.IntegerField(label='BB period')
    OPTIONS = (
        ('Upperband', 'Upperband'),
        ('Lowerband', 'Lowerband'),)
    bb_option = forms.ChoiceField(choices=OPTIONS, widget=forms.Select(), initial='Upperband')
    # bb_upperband = forms.FloatField(label='BB upperband')
    # bb_lowerband = forms.FloatField(label='BB lowerband')
    bb_std = forms.CharField(label='BB std')


class JobModule(DashboardModule):
    title = 'Jobs'
    template = 'dashboard_modules/job.html'
    layout = 'inline'
    children = []
    settings_form = JobSettingsForm
    child_form = JobItemForm
    child_name = 'Job'
    child_name_plural = 'Jobs'

    def __init__(self, title=None, children=list(), **kwargs):
        children = list(map(self.parse_job, children))
        kwargs.update({'children': children})
        super(JobModule, self).__init__(title, **kwargs)

    def settings_dict(self):
        return {
            'layout': self.layout
        }

    def load_settings(self, settings):
        self.layout = settings.get('layout', self.layout)

    def store_children(self):
        return True

    def parse_job(self, job):
        if isinstance(job, (tuple, list)):
            job_dict = {
                'title': job[0],
                'symbol': job[1],
                'interval': job[2],
                'rsi_period':job[3],
                'rsi_value':job[4],
                'bb_period':job[5],
                # 'bb_option':job[6],
                'bb_upperband':job[6],
                'bb_lowerband':job[7],
                'bb_std':job[8]
            }
            return job_dict
        elif isinstance(job, (dict,)):
            return job
