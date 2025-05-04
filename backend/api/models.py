from django.db import models

# Create your models here.


class Repository(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    avatar_url = models.URLField()
    url = models.URLField()
    summary = models.TextField()
    raw_data = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class Issue(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.URLField()
    raw_data = models.JSONField()
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Commit(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.URLField()
    raw_data = models.JSONField()
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class RepositoryWork(models.Model):
    id = models.AutoField(primary_key=True)
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    issues = models.ManyToManyField(Issue, blank=True)
    commits = models.ManyToManyField(Commit, blank=True)
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.repository.name} - {self.work_type}"
    
class Contributor(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255, unique=True)
    url = models.URLField()
    avatar_url = models.URLField()
    works = models.ManyToManyField(RepositoryWork, blank=True)
    summary = models.TextField()    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username
