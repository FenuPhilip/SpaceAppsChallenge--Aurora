from django import forms
from .models import UserStory

class UserStoryForm(forms.ModelForm):
    class Meta:
        model = UserStory
        fields = ['author_name', 'story_text']
        widgets = {
            'author_name': forms.TextInput(attrs={'placeholder': 'Your Name or Alias'}),
            'story_text': forms.Textarea(attrs={'placeholder': 'Share your experience...', 'rows': 4}),
        }
        labels = {
            'author_name': 'Your Name',
            'story_text': 'Your Story',
        }
