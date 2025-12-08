from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Student, Book, User, Librarian, POS, SystemSettings
import csv
from io import TextIOWrapper
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import Student



class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Student ID / Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Password'
        })
    )
##editedfrom django import forms
from django.core.exceptions import ValidationError
from .models import Student
import re

class StudentRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Confirm Password'
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Email Address'
        })
    )

    class Meta:
        model = Student
        fields = ['email', 'phone_number', 'profile_photo']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Phone Number'
            }),
            'profile_photo': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            })
        }

    def clean_password(self):
        password = self.cleaned_data.get('password')

        # Minimum 8 characters
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")

        # Uppercase
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must include at least one uppercase letter")

        # Lowercase
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must include at least one lowercase letter")

        # Number
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must include at least one number")

        # Special character
        if not re.search(r'[^A-Za-z0-9]', password):
            raise ValidationError("Password must include at least one special character")

        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match")

        return cleaned_data


    
class StudentIDVerificationForm(forms.Form):
    student_id = forms.CharField(
        label="Student ID",
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your Student ID'})
    )
####

class EmailVerificationForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-2xl tracking-widest',
            'placeholder': '000000',
            'maxlength': '6'
        })
    )


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'accept': '.csv'
        })
    )
    
    def clean_csv_file(self):
        file = self.cleaned_data['csv_file']
        if not file.name.endswith('.csv'):
            raise forms.ValidationError("Only CSV files are allowed")
        return file


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['isbn', 'title', 'author', 'category', 'publisher', 'year_published', 'copies_total', 'description', 'book_cover', 'price']
        widgets = {

            'isbn': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'author': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'category': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'publisher': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'year_published': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'copies_total': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg', 'rows': 4}),
            'book_cover': forms.FileInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            ###price
            'price': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded-lg p-2', 'step': '0.01'}),

        }


class POSForm(forms.ModelForm):
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
        required=False
    )
    
    class Meta:
        model = POS
        fields = ['name', 'serial_number', 'profile_photo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'serial_number': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'profile_photo': forms.FileInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
        }


class StudentSearchForm(forms.Form):
    student_id = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg text-center text-xl',
            'placeholder': 'Enter Student ID'
        })
    )


class ISBNSearchForm(forms.Form):
    isbn = forms.CharField(
        max_length=13,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg text-center text-xl',
            'placeholder': 'Enter ISBN'
        })
    )


class TransactionCodeForm(forms.Form):
    transaction_code = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg text-center text-xl',
            'placeholder': 'Enter Transaction Code'
        })
    )


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['student_id', 'last_name', 'first_name', 'middle_name', 'course', 'year', 'section', 'phone_number']
        widgets = {
            'student_id': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'middle_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'course': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'year': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'section': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
        }


class LibrarianForm(forms.ModelForm):
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
        required=False
    )
    
    class Meta:
        model = Librarian
        fields = ['name', 'email', 'profile_photo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'profile_photo': forms.FileInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
        }


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = ['system_name', 'system_logo']
        widgets = {
            'system_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'system_logo': forms.FileInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
        }
