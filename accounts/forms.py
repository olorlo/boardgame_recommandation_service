from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': '아이디 또는 비밀번호가 올바르지 않습니다.',
        'inactive': '비활성화된 계정입니다.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = '아이디'
        self.fields['username'].widget.attrs.update({
            'placeholder': '아이디를 입력하세요',
            'autocomplete': 'username',
        })
        self.fields['password'].label = '비밀번호'
        self.fields['password'].widget.attrs.update({
            'placeholder': '비밀번호를 입력하세요',
            'autocomplete': 'current-password',
        })

class CustomUserCreationForm(UserCreationForm):
    error_messages = {
        'password_mismatch': '비밀번호가 서로 일치하지 않습니다.',
    }

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = '아이디'
        self.fields['username'].help_text = ''
        self.fields['username'].widget.attrs.update({
            'placeholder': '사용할 아이디를 입력하세요',
            'autocomplete': 'username',
        })
        self.fields['username'].error_messages.update({
            'required': '아이디를 입력해주세요.',
            'unique': '이미 사용 중인 아이디입니다.',
            'max_length': '아이디는 150자 이하로 입력해주세요.',
        })

        self.fields['password1'].label = '비밀번호'
        self.fields['password1'].help_text = ''
        self.fields['password1'].widget.attrs.update({
            'placeholder': '비밀번호를 입력하세요',
            'autocomplete': 'new-password',
        })
        self.fields['password1'].error_messages.update({
            'required': '비밀번호를 입력해주세요.',
        })

        self.fields['password2'].label = '비밀번호 확인'
        self.fields['password2'].help_text = ''
        self.fields['password2'].widget.attrs.update({
            'placeholder': '비밀번호를 다시 입력하세요',
            'autocomplete': 'new-password',
        })
        self.fields['password2'].error_messages.update({
            'required': '비밀번호 확인을 입력해주세요.',
        })


class ProfileUpdateForm(forms.ModelForm):
    favorite_game_tags = forms.CharField(
        required=False,
        label='최애 보드게임 태그',
        help_text='최대 10개까지 입력할 수 있어요.',
        widget=forms.TextInput(
            attrs={
                'placeholder': '#스플렌더 #루미큐브 #카탄',
                'class': 'tag-input',
                'autocomplete': 'off',
            }
        ),
    )

    class Meta:
        model = User
        fields = ('profile_image', 'favorite_game_tags')
        labels = {
            'profile_image': '프로필 사진',
        }
        widgets = {
            'profile_image': forms.FileInput(attrs={'accept': 'image/*', 'class': 'profile-image-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_image'].required = False
        self.fields['profile_image'].help_text = '이미지 파일을 선택해주세요.'
        if self.instance and self.instance.favorite_game_tags:
            tags = self.instance.favorite_game_tag_list
            self.initial['favorite_game_tags'] = ' '.join(f'#{tag}' for tag in tags)

    def clean_favorite_game_tags(self):
        raw_tags = self.cleaned_data.get('favorite_game_tags', '')
        pieces = raw_tags.replace(',', ' ').split()
        tags = []

        for piece in pieces:
            tag = piece.strip().lstrip('#').strip()
            if not tag:
                continue
            if len(tag) > 30:
                raise forms.ValidationError('태그 하나는 30자 이하로 입력해주세요.')
            if tag not in tags:
                tags.append(tag)

        if len(tags) > 10:
            raise forms.ValidationError('최애 보드게임 태그는 최대 10개까지 입력할 수 있어요.')
        return ','.join(tags)

    def clean_profile_image(self):
        image = self.cleaned_data.get('profile_image')
        if image and hasattr(image, 'content_type') and not image.content_type.startswith('image/'):
            raise forms.ValidationError('프로필 사진은 이미지 파일만 업로드할 수 있어요.')
        return image


class AccountUpdateForm(UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = ('username',)
        labels = {
            'username': '아이디',
        }
        help_texts = {
            'username': '',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'placeholder': '아이디를 입력하세요',
            'autocomplete': 'username',
        })
        self.fields['username'].error_messages.update({
            'required': '아이디를 입력해주세요.',
            'unique': '이미 사용 중인 아이디입니다.',
            'max_length': '아이디는 150자 이하로 입력해주세요.',
        })
