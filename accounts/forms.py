from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

class CustomUserCreationForm(UserCreationForm):
    error_messages = {
        'password_mismatch': '비밀번호가 서로 일치하지 않습니다.',
    }

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
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
