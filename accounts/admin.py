from django.contrib import admin
from django.contrib.auth.models import Group
from .models import UserEmailConfirmation, UserPlan, UserPasswordConfirmation, UserSettings, UserSpamText
from .models import SiteSettings


admin.site.register(UserSpamText)
admin.site.register(UserEmailConfirmation)
admin.site.register(UserPlan)
admin.site.unregister(Group)
admin.site.register(UserPasswordConfirmation)
admin.site.register(SiteSettings)
admin.site.register(UserSettings)
