from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    mobile = models.BigIntegerField(_('Mobile'), blank=True, null=True)
    stories = models.ManyToManyField('Story', related_name='users', blank=True)
    last_reading = models.ForeignKey('Story', related_name='last_read_by', blank=True, null=True, on_delete=models.SET_NULL)
    favorites = models.ManyToManyField('Story', related_name='users_favorites', blank=True)

    def __str__(self):
        return self.username
    

class Story(models.Model):
    id=models.AutoField(primary_key=True)
    prompt=models.CharField(max_length=500)
    title=models.CharField(max_length=200)
    story=models.TextField()
    creation_date = models.DateTimeField(blank=True, null=True)
    image_url = models.CharField(max_length=400, null= True)
    reference_book = models.CharField(max_length=200, null= True)
    # moderation = models.BooleanField(default=True)
    user=models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def publish(self):
        self.creation_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title
    
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    story = models.ManyToManyField(Story, related_name='favorites', blank=True)
    creation_date = models.DateTimeField(blank=True, null=True)
    def publish(self):
        self.creation_date = timezone.now()
        self.save()

    
    