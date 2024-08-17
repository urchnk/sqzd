from django.db import models


class Text(models.Model):
    name = models.CharField(max_length=255, unique=True)
    text = models.TextField()
