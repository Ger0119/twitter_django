from django import forms


class TweetForm(forms.Form):
    keyword = forms.CharField(max_length=100, label='Keyword')
    items_count = forms.IntegerField(label='Count')
    like_count = forms.IntegerField(label='Like')
    search_start = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Search Start')
    search_end = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Search End')
