from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=300)
    summary = models.TextField(help_text="Short introduction for patients")
    content = models.TextField(help_text="Full article text")
    image = models.ImageField(upload_to='articles/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    published = models.BooleanField(default=True)

    def __str__(self):
        return self.title
