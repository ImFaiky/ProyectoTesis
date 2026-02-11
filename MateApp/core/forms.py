from django import forms
from .models import Discipline, Level
import json

DEFAULT_GAME_CONFIG = {
    "cards": {
        "question": {"text": "", "audio": "", "correct_answer": ""},
        "options": [{"text": "", "icon": ""} for _ in range(4)]
    },
    "option": {
        "question": {
            "text": "", "word": "", 
            "options": ["" for _ in range(4)], 
            "correct_answer": ""
        }
    },
    "dragDrop": {
        "question": {"text": "", "correct_order": [], "options": [], "sentence": ""}
    },
    "matchingGame": {
        "question": {"text": ""}, "pairs": []
    },
    "optionAudio": {
        "question": {
            "text": "", "audio": "", "correct_answer": "", 
            "options": ["" for _ in range(4)]
        }
    },
    "speech": {
        "question": {"text": "", "audio": ""}, "options": []
    },
    "writing": {
        "question": {"text": "", "correct_answer": ""}
    },
    "complete_word": {
        "question": {
            "text": "", "word": "", "missing_letters": [], 
            "correct_answer": "", "question_word": ""
        }
    }
}

class DisciplineForm(forms.ModelForm):
    class Meta:
        model = Discipline
        fields = ['name', 'description', 'color', 'difficulty', 'icon', 'is_active']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class LevelForm(forms.ModelForm):
    game_config_json = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 20, 'style': 'font-family: monospace;'}),
        help_text="Edit the game configuration as JSON.",
        initial=json.dumps(DEFAULT_GAME_CONFIG, indent=2)
    )

    class Meta:
        model = Level
        fields = ['number', 'is_active']

    def __init__(self, *args, **kwargs):
        discipline = kwargs.pop('discipline', None)
        super().__init__(*args, **kwargs)
        if discipline:
            self.instance.discipline = discipline
            
        if self.instance and self.instance.pk and self.instance.game_config:
            self.fields['game_config_json'].initial = json.dumps(self.instance.game_config, indent=2)

    def clean_game_config_json(self):
        data = self.cleaned_data['game_config_json']
        try:
            json_data = json.loads(data)
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f"Invalid JSON: {e}")
        return json_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.game_config = self.cleaned_data['game_config_json']
        if commit:
            instance.save()
        return instance
