from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(User)
admin.site.register(Author)
admin.site.register(Reader)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Follow)
