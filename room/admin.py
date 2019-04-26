from django.contrib import admin
from .models import UserActionType, UserAction, VKApiApplication, VKToken, VKAccount, VKGroup, VKSpamDialog, VKComment, VKClient, VKSpamDialogMessage



admin.site.register(UserActionType)
admin.site.register(UserAction)
admin.site.register(VKApiApplication)
admin.site.register(VKToken)
admin.site.register(VKClient)
admin.site.register(VKSpamDialogMessage)
admin.site.register(VKGroup)
admin.site.register(VKComment)
admin.site.register(VKSpamDialog)
admin.site.register(VKAccount)
