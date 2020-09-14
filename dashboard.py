from django.utils.translation import ugettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import Dashboard, AppIndexDashboard
from dashboard_modules import JobRecent, JobModule


class CustomIndexDashboard(Dashboard):
	columns = 2

	def init_with_context(self, context):
		self.children.append(modules.Feed(
			_('Latest News'),
				feed_url='http://www.djangoproject.com/rss/weblog/',
				limit=5,
				column=0,
				order=0
			))
		self.children.append(modules.RecentActions(
			_('Recent Actions'),
				10,
				column=0,
				order=0
			))
		self.children.append(JobModule(column=1))