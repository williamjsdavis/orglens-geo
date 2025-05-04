from django.contrib import admin
from .models import Repository, Issue, Commit, RepositoryWork, Contributor

# Register your models here.
admin.site.register(Repository)
admin.site.register(Issue)
admin.site.register(Commit)
admin.site.register(RepositoryWork)
admin.site.register(Contributor)