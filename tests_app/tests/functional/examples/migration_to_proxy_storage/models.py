# -*- coding: utf-8 -*-
from django.db import models


class JobApply(models.Model):
    resume = models.FileField(upload_to=lambda instance, filename: filename)

    class Meta:
        app_label = 'tests_app'