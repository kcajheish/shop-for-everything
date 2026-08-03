from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User
from django.forms.widgets import PasswordInput, EmailInput
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext_lazy as _

class SignUpForm(forms.Form):
    username = forms.CharField(label="使用者名稱")
    password = forms.CharField(widget=PasswordInput, label="輸入密碼")
    password_confirm = forms.CharField(widget=PasswordInput, label="再次輸入密碼")
    email = forms.CharField(widget=EmailInput, label="信箱")

    def clean_username(self):
        username = super().clean()['username']
        if " " in username:
            raise forms.ValidationError("不能有空白")
        if User.objects.filter(username=username).count():
            raise  forms.ValidationError("使用者重複")
        return username
    
    def clean(self):
        cd = super().clean()
        password = cd.get('password')
        password_confirm = cd.get('password_confirm')
        if password and password_confirm and (password != password_confirm):
            self.add_error('password_confirm',"輸入的密碼不一致，請重新輸入")
        return cd
    
    def save(self, commit=True):
        cd = super().clean()
        user = User(
            username=cd['username'],
            email=cd['email'],
        )
        user.set_password(cd['password'])
        if commit == True:
            user.save()
        return user

