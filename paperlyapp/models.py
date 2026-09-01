import uuid
from django.db import models
from django.contrib.auth.models import User


class PaperRequest(models.Model):
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("running", "Running"),
        ("done", "Done"),
        ("failed", "Failed")
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    topic = models.CharField(max_length=500)
    field = models.CharField(max_length=100)
    level = models.CharField(max_length=50)
    objectives = models.CharField(max_length=500)
    keywords = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    current_section = models.CharField(max_length=100, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_tokens_used = models.IntegerField(default=0)
    total_cost_usd = models.DecimalField(max_digits=8, decimal_places=4, default=0.0)

    def __str__(self):
        return f"{self.topic[:30]} ({self.status})"


class PaperSection(models.Model):
    paper = models.ForeignKey(PaperRequest, related_name="sections", on_delete=models.CASCADE)
    section_type = models.CharField(max_length=50)
    content = models.TextField()
    retry_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.paper.id} - {self.section_type}"


class GeneratedPaper(models.Model):
    request = models.OneToOneField(PaperRequest, on_delete=models.CASCADE, related_name="generated_paper")
    title = models.CharField(max_length=500)
    novelty = models.TextField()
    pdf_file = models.FileField(upload_to="papers/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
