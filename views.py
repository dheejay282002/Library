from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from datetime import timedelta
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.db.models import Sum, Count, Q
from .models import Book, Student, TransactionItem, Transaction
from django.contrib.auth.hashers import make_password
from django.db import models

import csv
from django.core.mail import send_mail
from django.conf import settings
from io import TextIOWrapper
from django.utils.crypto import get_random_string
from django.http import JsonResponse
from .forms import StudentRegistrationForm, EmailVerificationForm
from .models import Student, User, VerificationCode
import random
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction
import random
from datetime import timedelta
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils import timezone
from django.urls import reverse

from .models import Student, User, VerificationCode
from .forms import StudentRegistrationForm, EmailVerificationForm

from email.utils import formataddr
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from .models import Student, SystemSettings
from django.urls import reverse
# ✅ IMPORTS FIRST
from django.shortcuts import render, redirect
from django.contrib import messages
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils import timezone
from django.conf import settings
from .models import Student, SystemSettings
from .forms import StudentRegistrationForm
import random
from .models import Book, CartItem, Order



from .models import User, Student, Book, Transaction, VerificationCode, TransactionItem, Librarian, POS, SystemSettings, AdminLog
from .forms import (LoginForm, StudentIDVerificationForm, StudentRegistrationForm,
                   EmailVerificationForm, CSVUploadForm, BookForm, POSForm,
                   StudentSearchForm, ISBNSearchForm, TransactionCodeForm, StudentForm,
                   LibrarianForm, SystemSettingsForm)

import logging

logger = logging.getLogger(__name__)

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # 🔹 Check user type
                if user.user_type == 'student':
                    try:
                        student = user.student  # assuming OneToOneField
                        if not student.is_verified:
                            messages.error(request, 'Your email has not been verified. Please check your inbox.')
                            return redirect('email_verification')
                        if not student.is_approved:
                            messages.error(request, 'Your account is pending admin approval. Please wait until approved.')
                            return redirect('login')
                        if student.is_rejected:
                            messages.error(request, 'Your registration has been rejected. Contact admin for details.')
                            return redirect('login')
                    except Student.DoesNotExist:
                        messages.error(request, 'No student profile associated with this account.')
                        return redirect('login')
                
                # 🔹 Login allowed
                login(request, user)
                if user.user_type == 'admin':
                    return redirect('admin_dashboard')
                elif user.user_type == 'librarian':
                    return redirect('librarian_dashboard')
                elif user.user_type == 'pos':
                    return redirect('pos_home')
                else:  # student
                    return redirect('student_dashboard')
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = LoginForm()
    
    return render(request, 'library/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('login')


def verify_student_id(request):
    if request.method == 'POST':
        form = StudentIDVerificationForm(request.POST)
        if form.is_valid():
            student_id = form.cleaned_data['student_id']
            try:
                student = Student.objects.get(student_id=student_id)
                if student.user is not None:
                    messages.error(request, 'This student ID is already registered')
                    return redirect('verify_student_id')
                request.session['student_id'] = student_id
                return redirect('student_registration')
            except Student.DoesNotExist:
                messages.error(request, 'Student ID not found in the system. Please contact the admin.')
    else:
        form = StudentIDVerificationForm()
    
    return render(request, 'library/verify_student_id.html', {'form': form})

### register student



# 1️⃣ Define the helper function first
# 📩 Helper function to send verification email
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from .models import Student, User, VerificationCode, SystemSettings
from .forms import StudentRegistrationForm


# 📩 Helper function to send verification email
def send_verification_email(student, code):
    system_settings = SystemSettings.objects.first()
    system_name = system_settings.system_name if system_settings else "Library System"

    subject = f"{system_name} Email Verification"

    html_content = render_to_string('emails/email_verification.html', {
        'student': student,
        'verification_code': code,
        'system_name': system_name,
        'now': timezone.now(),
    })

    from_email = f"{system_name} <{settings.DEFAULT_FROM_EMAIL}>"

    email = EmailMessage(
        subject,
        html_content,
        from_email,
        [student.user.email],  # ✅ sends to student’s correct email
    )
    email.content_subtype = "html"
    email.send(fail_silently=False)



# 🧩 Student registration view
def student_registration(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('verify_student_id')

    student = get_object_or_404(Student, student_id=student_id)

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                with transaction.atomic():
                    student = form.save(commit=False)
                    student.save()

                    # ✅ Always update or create user
                    user, created = User.objects.get_or_create(username=student_id)
                    user.email = email  # always update student’s email
                    user.user_type = 'student'
                    user.is_active = False
                    user.set_password(password)
                    user.save()

                    student.user = user
                    student.save()

                    # ✅ Generate verification code and send email
                    code = VerificationCode.generate_code()
                    VerificationCode.objects.create(student=student, code=code)
                    send_verification_email(student, code)

                    # ✅ Store verification session
                    request.session['student_id_for_verification'] = student_id
                    request.session['registration_email'] = email
                    request.session['registration_password_hash'] = make_password(password)
                    request.session.pop('student_id', None)

                    messages.success(
                        request,
                        "Registration successful! We've sent a verification code to your email."
                    )
                    return redirect('email_verification')

            except Exception as e:
                messages.error(request, f"Registration failed: {str(e)}. Please try again.")

    else:
        form = StudentRegistrationForm(instance=student)

    return render(request, 'library/student_registration.html', {
        'form': form,
        'student': student
    })
    

def email_verification(request):
    student_id = request.session.get('student_id_for_verification')
    if not student_id:
        return redirect('verify_student_id')
    
    student = get_object_or_404(Student, student_id=student_id)
    email = request.session.get('registration_email')
    password_hash = request.session.get('registration_password_hash')
    
    if not email or not password_hash:
        messages.error(request, 'Session expired. Please register again.')
        return redirect('verify_student_id')
    
    if request.method == 'POST':
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                verification = VerificationCode.objects.get(
                    student=student,
                    code=code,
                    is_used=False
                )
                if verification.is_valid():
                    with transaction.atomic():
                        verification.is_used = True
                        verification.save()
                        
                        student.is_verified = True
                        student.save()
                        
                        user, created = User.objects.get_or_create(
                            username=student_id,
                            defaults={
                                'email': email,
                                'user_type': 'student',
                                'is_active': False
                            }
                        )
                        
                        if created:
                            user.password = password_hash
                            user.save()
                        
                        student.user = user
                        student.save()
                    
                    if 'student_id_for_verification' in request.session:
                        del request.session['student_id_for_verification']
                    if 'registration_email' in request.session:
                        del request.session['registration_email']
                    if 'registration_password_hash' in request.session:
                        del request.session['registration_password_hash']
                    
                    messages.success(request, 'Email verified successfully! Your account is pending admin approval. You will be able to login once approved.')
                    return redirect('login')
                else:
                    messages.error(request, 'Verification code has expired. Please request a new one.')
            except VerificationCode.DoesNotExist:
                messages.error(request, 'Invalid verification code')
    else:
        form = EmailVerificationForm()
    
    return render(request, 'library/email_verification.html', {'form': form, 'student': student})

def resend_verification_code(request):
    student_id = request.session.get('student_id_for_verification')
    if not student_id:
        return redirect('verify_student_id')
    
    student = get_object_or_404(Student, student_id=student_id)

    # Invalidate old codes
    VerificationCode.objects.filter(student=student, is_used=False).update(is_used=True)
    
    # Generate new code
    code = VerificationCode.generate_code()
    VerificationCode.objects.create(student=student, code=code)
    
    # Send HTML verification email
    send_verification_email(student, code)
    
    messages.success(request, 'A new verification code has been sent to your email.')
    return redirect('email_verification')
####
@login_required
def student_dashboard(request):
    if request.user.user_type != 'student':
        return redirect('dashboard')
    
    student = Student.objects.get(user=request.user)

    # Get latest library status (if none exists, assume open)
    library_status = LibraryStatus.objects.order_by('-updated_at').first()

    borrowed_books = Transaction.objects.filter(
        student=student,
        status='borrowed',
        approval_status='approved'
    ).prefetch_related('items__book')

    history = Transaction.objects.filter(
        student=student,
        approval_status='approved'
    ).prefetch_related('items__book').order_by('-borrowed_date')[:10]

    search_query = request.GET.get('search', '')
    category = request.GET.get('category', '')

    books = Book.objects.all()
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query)
        )
    if category:
        books = books.filter(category=category)

    categories = Book.objects.order_by('category').values_list('category', flat=True).distinct()

    returned_count = Transaction.objects.filter(
        student=student,
        status='returned',
        approval_status='approved'
    ).count()

    context = {
        'student': student,
        'borrowed_books': borrowed_books,
        'history': history,
        'books': books,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category,
        'returned_count': returned_count,
        'library_status': library_status,
    }

    return render(request, 'library/student_dashboard.html', context)


@login_required
def admin_dashboard(request):
    if request.user.user_type != 'admin':
        return redirect('dashboard')
    
    from .models import TransactionItem
    from django.db.models import Sum
    
    total_students = Student.objects.count()
    
    total_book_copies = Book.objects.aggregate(total=Sum('copies_total'))['total'] or 0
    total_borrowed = TransactionItem.objects.filter(
        status='borrowed',
        transaction__approval_status='approved'
    ).count()
    total_available = Book.objects.aggregate(total=Sum('copies_available'))['total'] or 0
    
    total_books = Book.objects.count()
    pending_registrations = Student.objects.filter(
        user__isnull=False,
        is_approved=False
    ).count()
    pending_borrowing = Transaction.objects.filter(
        approval_status='pending'
    ).count()
    
    # 🔧 Updated: exclude returned transactions
    recent_transactions = Transaction.objects.filter(
        approval_status='approved'
    ).exclude(
        status='returned'
    ).select_related(
        'student'
    ).prefetch_related(
        'items__book'
    ).order_by('-borrowed_date')[:10]
    
    context = {
        'total_students': total_students,
        'total_books': total_books,
        'total_borrowed': total_borrowed,
        'total_available': total_available,
        'pending_registrations': pending_registrations,
        'pending_borrowing': pending_borrowing,
        'recent_transactions': recent_transactions
    }
    
    return render(request, 'library/admin_dashboard.html', context)

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import LibraryStatus

@login_required
def library_status(request):
    if request.user.user_type != 'librarian':
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')

    latest_status = LibraryStatus.objects.last()

    if request.method == 'POST':
        status = request.POST.get('status')
        comment = request.POST.get('comment')
        LibraryStatus.objects.create(status=status, comment=comment)
        messages.success(request, f"Library status updated to '{status.capitalize()}'.")
        return redirect('library_status')

    return render(request, 'library/library_status.html', {'latest_status': latest_status})



@login_required
def import_books_csv(request):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                csv_file = request.FILES['csv_file']
                decoded_file = TextIOWrapper(csv_file.file, encoding='utf-8-sig')
                reader = csv.DictReader(decoded_file)
                
                success_count = 0
                error_count = 0
                errors_list = []
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        isbn = row.get('ISBN', row.get('isbn', '')).strip()
                        title = row.get('Book Name', row.get('Book name', row.get('title', ''))).strip()
                        author = row.get('Author', row.get('author', '')).strip()
                        category = row.get('Category', row.get('category', '')).strip()
                        publisher = row.get('Publisher', row.get('publisher', '')).strip()
                        year_published = row.get('Date Published', row.get('Date published', row.get('year_published', ''))).strip()
                        copies_total = row.get('Pieces', row.get('pieces', row.get('copies_total', '1'))).strip()
                        description = row.get('Description', row.get('description', '')).strip()
                        
                        if not isbn:
                            error_count += 1
                            errors_list.append(f'Row {row_num}: Missing ISBN')
                            continue
                        if not title:
                            error_count += 1
                            errors_list.append(f'Row {row_num}: Missing Book Name')
                            continue
                        if not author:
                            error_count += 1
                            errors_list.append(f'Row {row_num}: Missing Author')
                            continue
                        if not category:
                            error_count += 1
                            errors_list.append(f'Row {row_num}: Missing Category')
                            continue
                        
                        copies_num = 1
                        if copies_total:
                            if not copies_total.isdigit() or int(copies_total) < 1:
                                error_count += 1
                                errors_list.append(f'Row {row_num}: Invalid Pieces (must be positive integer)')
                                continue
                            copies_num = int(copies_total)
                        
                        year_num = None
                        if year_published:
                            if not year_published.isdigit():
                                error_count += 1
                                errors_list.append(f'Row {row_num}: Invalid Date Published (must be a number)')
                                continue
                            year_num = int(year_published)
                            if year_num < 1000 or year_num > 9999:
                                error_count += 1
                                errors_list.append(f'Row {row_num}: Invalid Date Published (must be 4 digits)')
                                continue
                        
                        book, created = Book.objects.get_or_create(
                            isbn=isbn,
                            defaults={
                                'title': title,
                                'author': author,
                                'category': category,
                                'publisher': publisher,
                                'year_published': year_num,
                                'copies_total': copies_num,
                                'copies_available': copies_num,
                                'description': description
                            }
                        )
                        if created:
                            success_count += 1
                            if request.user.user_type == 'librarian':
                                AdminLog.objects.create(
                                    librarian=request.user,
                                    action='book_import',
                                    description=f'Imported book: {title} (ISBN: {isbn})'
                                )
                        else:
                            error_count += 1
                            errors_list.append(f'Row {row_num}: Book with ISBN {isbn} already exists')
                    except Exception as e:
                        error_count += 1
                        errors_list.append(f'Row {row_num}: {str(e)}')
                
                if errors_list and len(errors_list) <= 10:
                    for error in errors_list:
                        messages.warning(request, error)
                elif errors_list:
                    messages.warning(request, f'Showing first 10 of {len(errors_list)} errors. Please check your CSV file.')
                    for error in errors_list[:10]:
                        messages.warning(request, error)
                
                messages.success(request, f'Successfully imported {success_count} books. {error_count} errors.')
                return redirect('manage_books')
            except KeyError as e:
                expected_format = 'ISBN, Book Name, Author, Date Published, Category, Pieces, Description'
                messages.error(request, f'Error: Missing required column in CSV file. Expected format: {expected_format}')
            except Exception as e:
                expected_format = 'ISBN, Book Name, Author, Date Published, Category, Pieces, Description'
                messages.error(request, f'Error processing CSV file: {str(e)}. Expected format: {expected_format}')
        else:
            messages.error(request, 'Invalid form submission. Please upload a valid CSV file.')
    else:
        form = CSVUploadForm()
    
    return render(request, 'library/import_books_csv.html', {'form': form})


@login_required
def import_students_csv(request):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                csv_file = request.FILES['csv_file']
                decoded_file = TextIOWrapper(csv_file.file, encoding='utf-8-sig')
                reader = csv.DictReader(decoded_file)
                
                success_count = 0
                error_count = 0
                errors_list = []
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        student_id = row.get('Student ID', row.get('student_id', '')).strip()
                        last_name = row.get('Last Name', row.get('last_name', '')).strip()
                        first_name = row.get('First Name', row.get('first_name', '')).strip()
                        middle_name = row.get('Middle Name', row.get('middle_name', '')).strip()
                        course = row.get('Course', row.get('course', '')).strip()
                        year = row.get('Year', row.get('year', '')).strip()
                        section = row.get('Section', row.get('section', '')).strip()
                        
                        if not student_id:
                            error_count += 1
                            errors_list.append(f'Row {row_num}: Missing Student ID')
                            continue
                        if not last_name:
                            error_count += 1
                            errors_list.append(f'Row {row_num}: Missing Last Name')
                            continue
                        if not first_name:
                            error_count += 1
                            errors_list.append(f'Row {row_num}: Missing First Name')
                            continue
                        if not course:
                            error_count += 1
                            errors_list.append(f'Row {row_num}: Missing Course')
                            continue
                        if not year:
                            error_count += 1
                            errors_list.append(f'Row {row_num}: Missing Year')
                            continue
                        if not section:
                            error_count += 1
                            errors_list.append(f'Row {row_num}: Missing Section')
                            continue
                        
                        student, created = Student.objects.get_or_create(
                            student_id=student_id,
                            defaults={
                                'last_name': last_name,
                                'first_name': first_name,
                                'middle_name': middle_name,
                                'course': course,
                                'year': year,
                                'section': section
                            }
                        )
                        if created:
                            success_count += 1
                            if request.user.user_type == 'librarian':
                                AdminLog.objects.create(
                                    librarian=request.user,
                                    action='student_import',
                                    description=f'Imported student: {last_name}, {first_name} (ID: {student_id})'
                                )
                        else:
                            error_count += 1
                            errors_list.append(f'Row {row_num}: Student ID {student_id} already exists')
                    except Exception as e:
                        error_count += 1
                        errors_list.append(f'Row {row_num}: {str(e)}')
                
                if errors_list and len(errors_list) <= 10:
                    for error in errors_list:
                        messages.warning(request, error)
                elif errors_list:
                    messages.warning(request, f'Showing first 10 of {len(errors_list)} errors. Please check your CSV file.')
                    for error in errors_list[:10]:
                        messages.warning(request, error)
                
                messages.success(request, f'Successfully imported {success_count} students. {error_count} errors.')
                if request.user.user_type == 'librarian':
                    return redirect('librarian_dashboard')
                return redirect('admin_dashboard')
            except KeyError as e:
                expected_format = 'Student ID, Last Name, First Name, Middle Name, Course, Year, Section'
                messages.error(request, f'Error: Missing required column in CSV file. Expected format: {expected_format}')
            except Exception as e:
                expected_format = 'Student ID, Last Name, First Name, Middle Name, Course, Year, Section'
                messages.error(request, f'Error processing CSV file: {str(e)}. Expected format: {expected_format}')
    else:
        form = CSVUploadForm()
    
    return render(request, 'library/import_students.html', {'form': form})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Book
from .forms import BookForm  # Make sure price field is in your BookForm

@login_required
def manage_books(request):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')
    
    from django.core.paginator import Paginator
    
    books = Book.objects.all().order_by('title')
    search_query = request.GET.get('search', '')
    
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query)
        )
    
    paginator = Paginator(books, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'library/manage_books.html', {
        'books': page_obj,
        'page_obj': page_obj,
        'search_query': search_query
    })


@login_required
def add_book(request):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.copies_available = book.copies_total
            book.save()
            messages.success(request, 'Book added successfully!')
            return redirect('manage_books')
    else:
        form = BookForm()
    
    return render(request, 'library/add_book.html', {'form': form})


@login_required
def edit_book(request, book_id):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')
    
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book updated successfully!')
            return redirect('manage_books')
    else:
        form = BookForm(instance=book)
    
    return render(request, 'library/edit_book.html', {'form': form, 'book': book})


@login_required
def manage_students(request):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')
    
    from django.core.paginator import Paginator
    
    pending_students = Student.objects.filter(user__isnull=False, is_approved=False).order_by('-created_at')
    
    students = Student.objects.all().order_by('last_name')
    search_query = request.GET.get('search', '')
    
    if search_query:
        students = students.filter(
            Q(student_id__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'library/manage_students.html', {
        'students': page_obj,
        'page_obj': page_obj,
        'pending_students': pending_students,
        'search_query': search_query
    })


@login_required


@login_required
def pending_students(request):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')
    
    pending = Student.objects.filter(user__isnull=False, is_approved=False).order_by('-created_at')
    
    return render(request, 'library/pending_students.html', {
        'pending_students': pending
    })


    
##reject student

def reject_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    # Mark student as rejected
    student.is_approved = False
    student.is_rejected = True
    student.save()

    messages.error(request, f"{student.get_full_name()} has been rejected.")
    return redirect('pending_students')
@login_required

# ✅ Approve Student
@login_required
def approve_student(request, student_id):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')

    student = get_object_or_404(Student, id=student_id)
    try:
        with transaction.atomic():
            # ✅ Update student approval status
            student.is_approved = True
            student.is_rejected = False
            student.save()

            # ✅ Activate the linked User account
            if student.user:
                student.user.is_active = True
                student.user.save()

            # 🔹 Get dynamic system name
            system_settings = SystemSettings.objects.first()
            system_name = system_settings.system_name if system_settings else "Library System"

            # 🔹 Email subject and content
            subject = f"{system_name} - Account Approved"
            html_content = render_to_string('emails/admin_approval.html', {
                'student': student,
                'login_url': request.build_absolute_uri(reverse('login')),
                'system_name': system_name,
                'now': timezone.now(),
            })

            # 🔹 Sender name = System Name only
            from_email = f"{system_name} <{settings.DEFAULT_FROM_EMAIL}>"

            # 🔹 Send email
            email = EmailMessage(
                subject=subject,
                body=html_content,
                from_email=from_email,
                to=[student.user.email],
            )
            email.content_subtype = "html"
            email.send(fail_silently=False)

        messages.success(request, f"{student.get_full_name()} approved and email sent successfully.")

    except Exception as e:
        messages.warning(request, f"{student.get_full_name()} approved, but email failed to send. Error: {str(e)}")

    return redirect('manage_students')

# ❌ Reject Student
@login_required
def reject_student(request, student_id):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')

    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        reason = request.POST.get('reason', 'No reason provided')
        student_name = student.get_full_name()

        try:
            with transaction.atomic():
                # Update rejection status
                student.is_approved = False
                student.is_rejected = True
                student.rejection_reason = reason
                student.save()

                # Delete linked user if exists
                if student.user:
                    user_email = student.user.email
                    student.user.delete()
                else:
                    user_email = None

                # Get system name dynamically
                system_settings = SystemSettings.objects.first()
                system_name = system_settings.system_name if system_settings else "Library System"

                # Email subject and body
                subject = f"{system_name} - Registration Rejected"
                html_content = render_to_string('emails/admin_rejection.html', {
                    'student': student,
                    'reason': reason,
                    'system_name': system_name,
                    'now': timezone.now(),
                })

                from_email = f"{system_name} <{settings.DEFAULT_FROM_EMAIL}>"

                if user_email:
                    email = EmailMessage(
                        subject=subject,
                        body=html_content,
                        from_email=from_email,
                        to=[user_email],
                    )
                    email.content_subtype = "html"
                    email.send(fail_silently=False)

            messages.success(request, f"Student {student_name} rejected and email sent successfully.")

        except Exception as e:
            messages.warning(request, f"Student {student_name} rejected, but email failed to send. Error: {str(e)}")

        return redirect('pending_students')

    return redirect('pending_students')
def manage_pos(request):
    if request.user.user_type != 'admin':
        return redirect('dashboard')
    
    pos_accounts = POS.objects.all().select_related('user')
    return render(request, 'library/manage_pos.html', {'pos_accounts': pos_accounts})

#### Start1###
@login_required
def add_pos(request):
    if request.user.user_type != 'admin':
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = POSForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            if User.objects.filter(username=username).exists():
                messages.error(request, f'Username "{username}" already exists. Please choose a different username.')
                return render(request, 'library/add_pos.html', {'form': form})
            
            if POS.objects.filter(serial_number=form.cleaned_data['serial_number']).exists():
                messages.error(request, f'Serial number "{form.cleaned_data["serial_number"]}" already exists. Please choose a different serial number.')
                return render(request, 'library/add_pos.html', {'form': form})
            
            user = User.objects.create_user(
                username=username,
                password=password,
                user_type='pos'
            )
            
            pos = form.save(commit=False)
            pos.user = user
            pos.save()
            
            messages.success(request, 'POS account created successfully!')
            return redirect('manage_pos')
    else:
        form = POSForm()
    
    return render(request, 'library/add_pos.html', {'form': form})


@login_required
def edit_pos(request, pos_id):
    if request.user.user_type != 'admin':
        return redirect('dashboard')
    
    pos = get_object_or_404(POS, id=pos_id)
    
    if request.method == 'POST':
        form = POSForm(request.POST, request.FILES, instance=pos)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data.get('password')
            
            if username != pos.user.username and User.objects.filter(username=username).exists():
                messages.error(request, f'Username "{username}" already exists. Please choose a different username.')
                return render(request, 'library/edit_pos.html', {'form': form, 'pos': pos})
            
            serial_number = form.cleaned_data['serial_number']
            if serial_number != pos.serial_number and POS.objects.filter(serial_number=serial_number).exists():
                messages.error(request, f'Serial number "{serial_number}" already exists. Please choose a different serial number.')
                return render(request, 'library/edit_pos.html', {'form': form, 'pos': pos})
            
            if password:
                pos.user.set_password(password)
            
            pos.user.username = username
            pos.user.save()
            
            form.save()
            messages.success(request, 'POS account updated successfully!')
            return redirect('manage_pos')
    else:
        form = POSForm(instance=pos, initial={'username': pos.user.username})
    
    return render(request, 'library/edit_pos.html', {'form': form, 'pos': pos})


@login_required
def delete_pos(request, pos_id):
    if request.user.user_type != 'admin':
        return redirect('dashboard')
    
    pos = get_object_or_404(POS, id=pos_id)
    
    if request.method == 'POST':
        pos_name = pos.name
        user = pos.user
        pos.delete()
        user.delete()
        messages.success(request, f'POS account "{pos_name}" deleted successfully!')
        return redirect('manage_pos')
    
    return render(request, 'library/delete_pos.html', {'pos': pos})


@login_required
def create_pos_account(request):
    return redirect('add_pos')


@login_required
def pos_home(request):
    if request.user.user_type != 'pos':
        return redirect('dashboard')
    
    return render(request, 'library/pos_home.html')

#####
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from .models import SystemSettings


# 📧 Unified email sender
def send_system_email(to_email, subject, template_name, context):
    """Reusable system email sender with system name as sender display."""
    system_settings = SystemSettings.objects.first()
    system_name = system_settings.system_name if system_settings else "Library System"

    context['system_name'] = system_name
    context['now'] = timezone.now()

    html_content = render_to_string(template_name, context)

    email = EmailMessage(
        subject=f"{system_name} - {subject}",
        body=html_content,
        from_email=f"{system_name} <{settings.DEFAULT_FROM_EMAIL}>",
        to=[to_email],
    )
    email.content_subtype = "html"
    email.send(fail_silently=False)


# ✅ Borrow Book View
@login_required
def pos_borrow_book(request):
    if request.user.user_type != 'pos':
        return redirect('dashboard')

    if request.method == 'POST':
        if 'student_id' in request.POST:
            student_id = request.POST.get('student_id')
            try:
                student = Student.objects.get(student_id=student_id, is_approved=True)
                request.session['pos_student_id'] = student_id
                request.session['pos_books'] = []
                return render(request, 'library/pos_borrow_book.html', {
                    'student': student,
                    'step': 'add_books'
                })
            except Student.DoesNotExist:
                messages.error(request, 'Student ID not found or not approved by admin')

        elif 'isbn' in request.POST:
            isbn = request.POST.get('isbn')
            student_id = request.session.get('pos_student_id')

            if not student_id:
                return redirect('pos_borrow_book')

            try:
                book = Book.objects.get(isbn=isbn)
                if not book.is_available():
                    messages.error(request, 'Book is not available')
                else:
                    books = request.session.get('pos_books', [])
                    books.append({
                        'id': book.id,
                        'isbn': book.isbn,
                        'title': book.title,
                        'author': book.author
                    })
                    request.session['pos_books'] = books
                    student = Student.objects.get(student_id=student_id)

                    if 'add_another' in request.POST:
                        return render(request, 'library/pos_borrow_book.html', {
                            'student': student,
                            'books': books,
                            'step': 'add_books'
                        })
                    else:
                        return render(request, 'library/pos_borrow_book.html', {
                            'student': student,
                            'books': books,
                            'step': 'confirm'
                        })
            except Book.DoesNotExist:
                messages.error(request, 'Book with this ISBN not found')
                student = Student.objects.get(student_id=student_id)
                return render(request, 'library/pos_borrow_book.html', {
                    'student': student,
                    'step': 'add_books'
                })

        elif 'confirm_borrow' in request.POST:
            student_id = request.session.get('pos_student_id')
            books_data = request.session.get('pos_books', [])

            if not student_id or not books_data:
                return redirect('pos_borrow_book')

            student = Student.objects.get(student_id=student_id)

            transaction_code = Transaction.generate_transaction_code()
            due_date = timezone.now() + timedelta(days=7)

            transaction = Transaction.objects.create(
                transaction_code=transaction_code,
                student=student,
                due_date=due_date,
                created_by=request.user
            )

            from .models import TransactionItem
            borrowed_books = []
            for book_data in books_data:
                book = Book.objects.get(id=book_data['id'])

                if book.is_available():
                    TransactionItem.objects.create(
                        transaction=transaction,
                        book=book
                    )
                    borrowed_books.append(book)

            del request.session['pos_student_id']
            del request.session['pos_books']

            # ✉️ Send Borrow Confirmation Email
            context = {
                'student': student,
                'transaction': transaction,
                'borrowed_books': borrowed_books,
                'due_date': due_date,
            }
            send_system_email(
                to_email=student.user.email,
                subject="Borrowing Confirmation",
                template_name='library/email_borrow.html',
                context=context
            )

            return render(request, 'library/pos_borrow_success.html', {
                'student': student,
                'transaction': transaction
            })

    return render(request, 'library/pos_borrow_book.html', {'step': 'student_id'})


# ✅ Return Book View
@login_required
def pos_return_book(request):
    if request.user.user_type != 'pos':
        return redirect('dashboard')

    if request.method == 'POST':
        if 'transaction_code' in request.POST:
            transaction_code = request.POST.get('transaction_code')
            transaction = Transaction.objects.filter(
                transaction_code__startswith=transaction_code,
                approval_status='approved'
            ).select_related('student').prefetch_related('items__book').first()

            if transaction:
                borrowed_items = transaction.items.filter(status='borrowed')
                if borrowed_items.exists():
                    return render(request, 'library/pos_return_book.html', {
                        'transaction': transaction,
                        'borrowed_items': borrowed_items,
                        'step': 'confirm'
                    })
                else:
                    messages.error(request, 'All books from this transaction have already been returned')
            else:
                messages.error(request, 'No borrowing found with this transaction code')

        elif 'return_books' in request.POST:
            transaction_code = request.POST.get('transaction_code_value')
            selected_items = request.POST.getlist('selected_books')

            if transaction_code and selected_items:
                from .models import TransactionItem
                transaction = Transaction.objects.filter(
                    transaction_code=transaction_code,
                    approval_status='approved'
                ).prefetch_related('items__book').first()

                if transaction:
                    returned_items = []
                    unreturned_items = []

                    for item in transaction.items.filter(status='borrowed'):
                        if str(item.id) in selected_items:
                            item.status = 'returned'
                            item.return_date = timezone.now()
                            item.save()

                            item.book.copies_available += 1
                            item.book.save()
                            returned_items.append(item)
                        else:
                            unreturned_items.append(item)

                    all_returned = not transaction.items.filter(status='borrowed').exists()
                    if all_returned:
                        transaction.status = 'returned'
                        transaction.return_date = timezone.now()
                        transaction.save()

                    # ✉️ Send Return Confirmation Email
                    context = {
                        'student': transaction.student,
                        'transaction': transaction,
                        'returned_items': returned_items,
                        'unreturned_items': unreturned_items,
                    }
                    send_system_email(
                        to_email=transaction.student.user.email,
                        subject="Return Confirmation",
                        template_name='library/email_return.html',
                        context=context
                    )

                    # ✅ Render success page
                    return render(request, 'library/pos_return_success.html', {
                        'student': transaction.student,
                        'transaction': transaction,
                        'returned_items': returned_items,
                        'unreturned_items': unreturned_items,
                        'all_returned': all_returned
                    })
            else:
                messages.error(request, 'Please select at least one book to return')
                return redirect('pos_return_book')

    return render(request, 'library/pos_return_book.html', {'step': 'transaction_code'})

#######

@login_required
def pending_transactions(request):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')
    
    pending = Transaction.objects.filter(approval_status='pending').select_related('student', 'created_by').prefetch_related('items__book').order_by('-borrowed_date')
    
    return render(request, 'library/pending_transactions.html', {
        'pending_transactions': pending
    })

@login_required
def approve_transaction(request, transaction_id):
    from django.contrib import messages
    transaction = get_object_or_404(Transaction, id=transaction_id)

    # Only allow approval if it’s pending
    if transaction.approval_status != 'pending':
        messages.error(request, "This transaction has already been processed.")
        return redirect('pending_transactions')

    # Check each book’s availability
    unavailable_books = []
    for item in transaction.items.all():
        if item.book.copies_available <= 0:
            unavailable_books.append(item.book.title)

    if unavailable_books:
        message = (
            "Cannot approve this request. "
            "The following book(s) have no available copies: "
            + ", ".join(unavailable_books)
        )
        messages.error(request, message)
        return redirect('pending_transactions')

    # If all books are available → approve
    for item in transaction.items.all():
        item.status = 'borrowed'
        item.book.copies_available -= 1
        item.book.save()
        item.save()

    transaction.approval_status = 'approved'
    transaction.borrowed_date = timezone.now()
    transaction.due_date = timezone.now() + timedelta(days=7)
    transaction.save()

    messages.success(request, "Transaction approved successfully.")
    return redirect('pending_transactions')

@login_required
def reject_transaction(request, transaction_id):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')
    
    if request.method == 'POST':
        transaction = Transaction.objects.get(id=transaction_id)
        
        transaction.approval_status = 'rejected'
        transaction.approved_by = request.user
        transaction.approved_at = timezone.now()
        transaction.save()
        
        messages.success(request, f'Book borrowing request rejected')
    
    return redirect('pending_transactions')


@login_required
def dashboard(request):
    if request.user.user_type == 'admin':
        return redirect('admin_dashboard')
    elif request.user.user_type == 'librarian':
        return redirect('librarian_dashboard')
    elif request.user.user_type == 'pos':
        return redirect('pos_home')
    else:
        return redirect('student_dashboard')


@login_required
def student_settings(request):
    if request.user.user_type != 'student':
        return redirect('dashboard')
    
    student = Student.objects.get(user=request.user)
    
    if request.method == 'POST':
        student.phone_number = request.POST.get('phone_number', student.phone_number)
        
        if 'profile_photo' in request.FILES:
            student.profile_photo = request.FILES['profile_photo']
        
        email = request.POST.get('email')
        if email and email != request.user.email:
            request.user.email = email
            request.user.save()
        
        password = request.POST.get('password')
        if password:
            request.user.set_password(password)
            request.user.save()
            messages.success(request, 'Password updated. Please login again.')
            return redirect('login')
        
        student.save()
        messages.success(request, 'Settings updated successfully!')
        return redirect('student_settings')
    
    return render(request, 'library/student_settings.html', {'student': student})


@login_required
def admin_settings(request):
    if request.user.user_type != 'admin':
        return redirect('dashboard')
    
    system_settings = SystemSettings.get_settings()
    
    if request.method == 'POST':
        if 'update_system' in request.POST:
            form = SystemSettingsForm(request.POST, request.FILES, instance=system_settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'System settings updated successfully!')
                return redirect('admin_settings')
        else:
            email = request.POST.get('email')
            if email:
                request.user.email = email
                request.user.save()
            
            password = request.POST.get('password')
            if password:
                request.user.set_password(password)
                request.user.save()
                messages.success(request, 'Password updated. Please login again.')
                return redirect('login')
            
            messages.success(request, 'Settings updated successfully!')
            return redirect('admin_settings')
    else:
        form = SystemSettingsForm(instance=system_settings)
    
    return render(request, 'library/admin_settings.html', {
        'form': form,
        'system_settings': system_settings
    })


@login_required
def delete_book(request, book_id):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')
    
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        book_title = book.title
        book.delete()
        messages.success(request, f'Book "{book_title}" deleted successfully!')
        return redirect('manage_books')
    
    return render(request, 'library/delete_book.html', {'book': book})


@login_required
def add_student(request):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student added successfully!')
            return redirect('manage_students')
    else:
        form = StudentForm()
    
    return render(request, 'library/add_student.html', {'form': form})


@login_required
def edit_student(request, student_id):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')
    
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('manage_students')
    else:
        form = StudentForm(instance=student)
    
    return render(request, 'library/edit_student.html', {'form': form, 'student': student})


@login_required
def delete_student(request, student_id):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')
    
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        student_name = student.get_full_name()
        if student.user:
            student.user.delete()
        student.delete()
        messages.success(request, f'Student "{student_name}" deleted successfully!')
        return redirect('manage_students')
    
    return render(request, 'library/delete_student.html', {'student': student})


@login_required
def student_books(request):
    if request.user.user_type != 'student':
        return redirect('dashboard')
    
    from django.core.paginator import Paginator
    
    search_query = request.GET.get('search', '')
    category = request.GET.get('category', '')
    
    books = Book.objects.all()
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query)
        )
    if category:
        books = books.filter(category=category)
    
    categories = Book.objects.order_by('category').values_list('category', flat=True).distinct()
    
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    student = Student.objects.get(user=request.user)
    
    context = {
        'books': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category,
        'student': student
    }
    
    return render(request, 'library/student_books.html', context)


@login_required
def export_books_by_category(request):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')
    
    import csv
    from django.http import HttpResponse
    
    category = request.GET.get('category', '')
    
    response = HttpResponse(content_type='text/csv')
    if category:
        response['Content-Disposition'] = f'attachment; filename="books_{category}.csv"'
        books = Book.objects.filter(category=category)
    else:
        response['Content-Disposition'] = 'attachment; filename="all_books.csv"'
        books = Book.objects.all()
    
    writer = csv.writer(response)
    writer.writerow(['ISBN', 'Title', 'Author', 'Category', 'Publisher', 'Year', 'Copies Total', 'Copies Available'])
    
    for book in books:
        writer.writerow([
            book.isbn,
            book.title,
            book.author,
            book.category,
            book.publisher or '',
            book.year_published or '',
            book.copies_total,
            book.copies_available
        ])
    
    return response


@login_required
def librarian_dashboard(request):
    if request.user.user_type != 'librarian':
        return redirect('dashboard')
    
    from .models import TransactionItem
    from django.db.models import Sum
    
    total_students = Student.objects.count()
    
    total_book_copies = Book.objects.aggregate(total=Sum('copies_total'))['total'] or 0
    total_borrowed = TransactionItem.objects.filter(
        status='borrowed',
        transaction__approval_status='approved'
    ).count()
    total_available = Book.objects.aggregate(total=Sum('copies_available'))['total'] or 0
    
    total_books = Book.objects.count()
    pending_registrations = Student.objects.filter(
        user__isnull=False,
        is_approved=False
    ).count()
    pending_borrowing = Transaction.objects.filter(
        approval_status='pending'
    ).count()
    
    recent_transactions = Transaction.objects.filter(
        approval_status='approved'
    ).exclude(
        status='returned'
    ).select_related(
        'student'
    ).prefetch_related(
        'items__book'
    ).order_by('-borrowed_date')[:10]
    
    context = {
        'total_students': total_students,
        'total_books': total_books,
        'total_borrowed': total_borrowed,
        'total_available': total_available,
        'pending_registrations': pending_registrations,
        'pending_borrowing': pending_borrowing,
        'recent_transactions': recent_transactions
    }
    
    return render(request, 'library/librarian_dashboard.html', context)


@login_required
def manage_librarians(request):
    if request.user.user_type != 'admin':
        return redirect('dashboard')
    
    librarians = Librarian.objects.all().select_related('user')
    return render(request, 'library/manage_librarians.html', {'librarians': librarians})


@login_required
def add_librarian(request):
    if request.user.user_type != 'admin':
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LibrarianForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            user = User.objects.create_user(
                username=username,
                password=password,
                user_type='librarian',
                email=form.cleaned_data['email']
            )
            
            librarian = form.save(commit=False)
            librarian.user = user
            librarian.save()
            
            messages.success(request, 'Librarian added successfully!')
            return redirect('manage_librarians')
    else:
        form = LibrarianForm()
    
    return render(request, 'library/add_librarian.html', {'form': form})


@login_required
def edit_librarian(request, librarian_id):
    if request.user.user_type != 'admin':
        return redirect('dashboard')
    
    librarian = get_object_or_404(Librarian, id=librarian_id)
    
    if request.method == 'POST':
        form = LibrarianForm(request.POST, request.FILES, instance=librarian)
        if form.is_valid():
            password = form.cleaned_data.get('password')
            
            if password:
                librarian.user.set_password(password)
            
            librarian.user.username = form.cleaned_data['username']
            librarian.user.email = form.cleaned_data['email']
            librarian.user.save()
            
            form.save()
            messages.success(request, 'Librarian updated successfully!')
            return redirect('manage_librarians')
    else:
        form = LibrarianForm(instance=librarian, initial={'username': librarian.user.username})
    
    return render(request, 'library/edit_librarian.html', {'form': form, 'librarian': librarian})


@login_required
def delete_librarian(request, librarian_id):
    if request.user.user_type != 'admin':
        return redirect('dashboard')
    
    librarian = get_object_or_404(Librarian, id=librarian_id)
    
    if request.method == 'POST':
        librarian_name = librarian.name
        user = librarian.user
        librarian.delete()
        user.delete()
        messages.success(request, f'Librarian "{librarian_name}" deleted successfully!')
        return redirect('manage_librarians')
    
    return render(request, 'library/delete_librarian.html', {'librarian': librarian})

@login_required
def admin_logs(request):
    if request.user.user_type != 'admin':
        return redirect('dashboard')
    
    from django.core.paginator import Paginator
    
    librarian_filter = request.GET.get('librarian', '')
    
    logs = AdminLog.objects.select_related('librarian').all()
    
    if librarian_filter:
        logs = logs.filter(librarian__id=librarian_filter)
    
    librarians = User.objects.filter(user_type='librarian')
    
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'logs': page_obj,
        'page_obj': page_obj,
        'librarians': librarians,
        'selected_librarian': librarian_filter
    }
    
    return render(request, 'library/admin_logs.html', context)

@login_required
def student_books(request):
    if request.user.user_type != 'student':
        return redirect('dashboard')
    
    from django.core.paginator import Paginator
    
    search_query = request.GET.get('search', '')
    selected_category = request.GET.get('category', '')
    
    books = Book.objects.filter(copies_total__gt=0).order_by('title')
    
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query)
        )
    
    if selected_category:
        books = books.filter(category=selected_category)
    
    categories = Book.objects.order_by('category').values_list('category', flat=True).distinct()
    
    paginator = Paginator(books, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'books': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': selected_category,
    }
    
    return render(request, 'library/student_books.html', context)


@login_required
def download_books_csv_template(request):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')
    
    from django.http import HttpResponse
    import csv
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="books_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ISBN', 'Book Name', 'Author', 'Date Published', 'Category', 'Pieces', 'Description'])
    writer.writerow(['978-0-123456-78-9', 'Sample Book Title', 'John Doe', '2023', 'Fiction', '5', 'This is a sample book description'])
    
    return response


@login_required
def download_students_csv_template(request):
    if request.user.user_type not in ['admin', 'librarian']:
        return redirect('dashboard')
    
    from django.http import HttpResponse
    import csv
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student ID', 'Last Name', 'First Name', 'Middle Name', 'Course', 'Year', 'Section'])
    writer.writerow(['2024-12345', 'Dela Cruz', 'Juan', 'Santos', 'BSIT', '1', 'A'])
    
    return response


from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib import messages
from .models import Transaction, TransactionItem, Student, Book
from django.utils import timezone
from datetime import timedelta

def borrow_request(request):
    if request.method == 'POST':
        student = get_object_or_404(Student, user=request.user)
        book_ids = request.POST.getlist('book_ids')  # e.g. a list of selected books

        # Create a new transaction
        transaction = Transaction.objects.create(
            student=student,
            due_date=timezone.now() + timedelta(days=7),
            status='Pending Approval'
        )

        # Add borrowed books
        for book_id in book_ids:
            book = get_object_or_404(Book, id=book_id)
            TransactionItem.objects.create(transaction=transaction, book=book)

        # Prepare email
        subject = f"Library Borrowing Invoice - {transaction.transaction_code}"
        html_message = render_to_string('library/email_invoice.html', {
            'student': student,
            'transaction': transaction,
        })
        plain_message = strip_tags(html_message)
        to = [student.user.email]

        # Send email
        send_mail(subject, plain_message, None, to, html_message=html_message)

        messages.success(request, "Borrowing request submitted successfully. An invoice has been emailed to you.")
        return redirect('borrowing_success', transaction_id=transaction.id)

    return redirect('student_books')


from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Transaction, TransactionItem

def return_books(request):
    if request.method == 'POST':
        transaction_code = request.POST.get('transaction_code')
        transaction = get_object_or_404(Transaction, transaction_code=transaction_code)
        student = transaction.student

        # Mark all borrowed books as returned
        returned_items = []
        for item in transaction.items.filter(returned=False):
            item.returned = True
            item.save()
            returned_items.append(item)

        # Update transaction status if all are returned
        if not transaction.items.filter(returned=False).exists():
            transaction.status = 'Returned'
            transaction.save()

        # Prepare email content
        subject = f"Library Return Receipt - {transaction.transaction_code}"
        html_message = render_to_string('library/email_return.html', {
            'student': student,
            'transaction': transaction,
            'returned_items': returned_items,
        })
        plain_message = strip_tags(html_message)
        to = [student.user.email]

        # Send the return confirmation email
        send_mail(subject, plain_message, None, to, html_message=html_message)

        messages.success(request, "Books successfully returned. A confirmation email has been sent to the borrower.")
        return redirect('pos_return_success')

    return redirect('pos_home')


## verify email
from django.shortcuts import render
from django.http import JsonResponse

def verify_email(request):
    if request.method == 'POST':
        code = request.POST.get('verification_code')
        # Replace this with your actual verification logic
        if code == '1234':  # temporary dummy code
            return JsonResponse({'success': True, 'message': 'Email verified!'})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid code.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})






from django.shortcuts import render, redirect
from .models import LibraryStatus

def library_status_view(request):
    # Handle manual form submission
    if request.method == "POST" and "manual_update_btn" in request.POST:
        status = request.POST.get("status")
        comment = request.POST.get("comment", "")
        LibraryStatus.objects.create(status=status, comment=comment)
        return redirect('library_status')  # Redirect ensures latest status is displayed

    # Get the latest status
    library_status = LibraryStatus.objects.order_by('-updated_at').first()

    return render(request, 'library_status.html', {'library_status': library_status})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Book, CartItem, Order, OrderItem
from django.db.models import F, Sum
from django.http import JsonResponse

# Add to cart
# Add to Cart
def add_to_cart(request, book_id):
    cart = request.session.get('cart', {})
    cart[str(book_id)] = cart.get(str(book_id), 0) + 1
    request.session['cart'] = cart
    return redirect('cart')  # Redirect to cart page
from django.shortcuts import render

def browse_books(request):
    # your logic here
    return render(request, 'library/browse_books.html')

from django.shortcuts import render

def browse_books(request):
    # Fetch books from your database (example)
    books = Book.objects.all()  # assuming you have a Book model
    return render(request, 'library/browse_books.html', {'books': books})

# View Cart
def cart_view(request):
    cart = request.session.get('cart', {})
    books = []
    total_price = 0
    for book_id, qty in cart.items():
        book = get_object_or_404(Book, id=book_id)
        books.append({'book': book, 'qty': qty, 'subtotal': book.price * qty})
        total_price += book.price * qty
    return render(request, 'library/cart.html', {'books': books, 'total_price': total_price})

# Cart page
@login_required
def cart(request):
    if request.user.user_type != 'student':
        return redirect('dashboard')
    
    cart_items = CartItem.objects.filter(student=request.user)
    
    if request.method == 'POST':
        # Update quantities and selected books
        for item in cart_items:
            qty = request.POST.get(f'quantity_{item.id}')
            sel = request.POST.get(f'select_{item.id}') == 'on'
            if qty:
                item.quantity = int(qty)
            item.selected = sel
            item.save()
        messages.success(request, 'Cart updated!')
        return redirect('cart')
    
    total = sum([item.subtotal() for item in cart_items if item.selected])
    return render(request, 'library/cart.html', {'cart_items': cart_items, 'total': total})


@login_required
def view_cart(request):
    if request.user.user_type != 'student':
        return redirect('dashboard')

    cart_items = CartItem.objects.filter(student=request.user)
    total_price = sum([item.subtotal() for item in cart_items])

    return render(request, 'library/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })

@login_required
def student_orders(request):
    if request.user.user_type != 'student':
        return redirect('dashboard')
    orders = Order.objects.filter(student=request.user).order_by('-created_at')
    return render(request, 'library/student_orders.html', {'orders': orders})


# Checkout page
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('cart')
# Student orders page
@login_required
def librarian_orders(request):
    if request.user.user_type not in ['librarian', 'admin']:
        return redirect('dashboard')
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'library/librarian_orders.html', {'orders': orders})
    return render(request, 'library/student_orders.html', {'orders': orders})

# Librarian order management
@login_required
def manage_orders(request):
    if request.user.user_type != 'librarian':
        return redirect('dashboard')
    orders = Order.objects.all().order_by('-created_at')
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        status = request.POST.get('status')
        order = get_object_or_404(Order, id=order_id)
        order.status = status
        order.save()
        messages.success(request, f'Order {order.id} updated!')
        return redirect('manage_orders')
    return render(request, 'library/manage_orders.html', {'orders': orders})

@login_required
def gcash_payment(request, order_id):
    if request.user.user_type != 'student':
        return redirect('dashboard')

    order = get_object_or_404(Order, id=order_id, student=request.user)

    if request.method == 'POST':
        # Here we would integrate real payment API
        # For mock, we just mark order as Paid (Processing)
        order.status = 'Processing'
        order.save()
        messages.success(request, 'Payment successful! Your order is now being processed.')
        return redirect('student_orders')

    return render(request, 'library/gcash_payment.html', {'order': order})

@login_required
def cancel_order(request, order_id):
    if request.user.user_type != 'student':
        return redirect('dashboard')

    order = get_object_or_404(Order, id=order_id, student=request.user)
    if order.status in ['Pending', 'Processing']:
        order.status = 'Cancelled'
        order.save()
        messages.success(request, 'Your order has been cancelled.')
    else:
        messages.error(request, 'Cannot cancel this order.')

    return redirect('student_orders')

@login_required
def librarian_orders(request):
    if request.user.user_type != 'librarian':
        return redirect('dashboard')
    
    orders = Order.objects.all().order_by('-created_at')  # newest first
    return render(request, 'library/librarian_orders.html', {'orders': orders})

@login_required
def fetch_orders_librarian(request):
    if request.user.user_type != 'librarian':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    orders = Order.objects.filter(status__in=['pending', 'processing', 'ready', 'delivered']).order_by('-created_at')
    html = render_to_string('library/orders_table_rows.html', {'orders': orders})
    
    pending_count = orders.filter(status='pending').count()
    
    return JsonResponse({'html': html, 'pending_orders': pending_count})


@login_required
def update_order_status(request, order_id, status):
    if request.user.user_type not in ['librarian', 'admin']:
        return redirect('dashboard')
    order = get_object_or_404(Order, id=order_id)
    order.status = status
    order.save()
    messages.success(request, f"Order {order.id} status updated to {status}.")
    return redirect('librarian_orders')

from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

@login_required
def new_orders_count(request):
    if request.user.user_type != 'librarian':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    # Count orders in 'Pending' status
    pending_orders = Order.objects.filter(status='Pending').count()
    return JsonResponse({'pending_orders': pending_orders})

@login_required
def update_cart(request):
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                cart_id = int(key.split('_')[1])
                cart_item = CartItem.objects.get(id=cart_id, student=request.user)
                cart_item.quantity = int(value)
                cart_item.save()
    return redirect('view_cart')


@login_required
def checkout(request):
    if request.method == 'POST':
        selected_items = request.POST.getlist('selected')
        payment_method = request.POST.get('payment_method')
        address = request.POST.get('address', '')

        items = CartItem.objects.filter(id__in=selected_items, student=request.user)
        total_price = sum([item.subtotal() for item in items])

        order = Order.objects.create(
            student=request.user,
            total_price=total_price,
            payment_method=payment_method,
            address=address if payment_method == 'cod' else ''
        )
        order.items.set(items)
        order.save()

        # Clear purchased items from cart
        items.delete()

        if payment_method == 'gcash':
            # redirect to GCash payment page
            return redirect('gcash_payment', order_id=order.id)
        
        messages.success(request, 'Order placed successfully!')
        return redirect('student_orders')
    
    return redirect('view_cart')


import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def update_cart_ajax(request):
    if request.method == 'POST' and request.user.user_type == 'student':
        data = json.loads(request.body)
        cart_id = data.get('cart_id')
        action = data.get('action')

        try:
            cart_item = CartItem.objects.get(id=cart_id, student=request.user)
            if action == 'increase':
                cart_item.quantity += 1
            elif action == 'decrease' and cart_item.quantity > 1:
                cart_item.quantity -= 1
            cart_item.save()

            # Update total
            cart_items = CartItem.objects.filter(student=request.user)
            total_price = sum([item.subtotal() for item in cart_items])

            return JsonResponse({
                'success': True,
                'quantity': cart_item.quantity,
                'subtotal': cart_item.subtotal(),
                'total_price': total_price
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Student  # adjust model name if needed


##### start here####

@csrf_exempt
def verify_student(request):
    if request.method == "POST":
        data = json.loads(request.body)
        student_id = data.get("student_id", "").strip()
        try:
            student = Student.objects.get(student_id=student_id)
            return JsonResponse({
                "exists": True,
                "name": student.get_full_name(),
                "student_id": student.student_id
            })
        except Student.DoesNotExist:
            return JsonResponse({"exists": False})
    return JsonResponse({"error": "Invalid request"}, status=400)


####here####

# views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from .models import Student

@login_required
def validate_student_id(request):
    student_id = request.GET.get('student_id', '').strip()
    try:
        student = Student.objects.get(student_id=student_id)
        if student.is_approved:
            return JsonResponse({"valid": True, "approved": True})
        else:
            return JsonResponse({"valid": True, "approved": False, "reason": "You must register first."})
    except Student.DoesNotExist:
        return JsonResponse({"valid": False, "approved": False, "reason": "Student not registered."})


from django.shortcuts import render, redirect
from .models import Student

def pos_options(request):
    student_id = request.GET.get('student_id')
    if not student_id:
        return redirect('pos_student_login')  # send back if missing

    try:
        student = Student.objects.get(student_id=student_id)
        if not student.is_approved:
            return redirect('pos_student_login')
    except Student.DoesNotExist:
        return redirect('pos_student_login')

    # ✅ If we reach here, student is valid
    return render(request, 'library/pos_options.html', {
        'student': student
    })


from django.shortcuts import render, redirect
from .models import Student

def pos_options(request):
    # Try to get student_id from GET or session
    student_id = request.GET.get('student_id') or request.session.get('student_id')
    if not student_id:
        print("⚠ No student_id found, redirecting to POS login")
        return redirect('pos_student_login')  # go back if missing

    try:
        student = Student.objects.get(student_id=student_id)
        if not student.is_approved:
            print("⚠ Student not approved, redirecting")
            return redirect('pos_student_login')
    except Student.DoesNotExist:
        print("❌ Student not found, redirecting")
        return redirect('pos_student_login')

    # ✅ Keep session active for POS navigation
    request.session['student_id'] = student.student_id

    print("✅ Access granted to:", student.get_full_name())
    return render(request, 'library/pos_options.html', {'student': student})


#####BORROW BOOKS

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Student, Book, Transaction, TransactionItem
import re
@login_required
@csrf_exempt
def pos_borrow_book(request):
    if request.user.user_type != 'pos':
        return redirect('dashboard')

    student_id = request.GET.get('student_id') or request.session.get('pos_student_id')
    if not student_id:
        return redirect('pos_home')

    try:
        student = Student.objects.get(student_id=student_id, is_approved=True)
        request.session['pos_student_id'] = student_id
    except Student.DoesNotExist:
        messages.error(request, 'Student not found or not approved.')
        return redirect('pos_home')

    # Ensure the session list exists
    if 'pos_books' not in request.session:
        request.session['pos_books'] = []
    books = request.session['pos_books']

  # ✅ Remove book handler (must come early)
    if request.method == 'POST' and ('remove_book' in request.POST or request.POST.get('action') == 'remove'):
        try:
            book_id = int(request.POST.get('book_id'))
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid book ID'}, status=400)

        books = [b for b in books if b['id'] != book_id]
        request.session['pos_books'] = books
        request.session.modified = True

        # If AJAX, return JSON instead of HTML
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'books': books})

        # Otherwise normal render (for non-JS fallback)
        messages.success(request, 'Book removed.')
        return render(request, 'library/pos_borrow_book.html', {
            'student': student,
            'books': books,
            'step': 'add_books'
        })

    # ✅ Add book via AJAX (for scanners)
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        isbn_raw = request.POST.get('isbn', '').strip()
        if not isbn_raw:
            return JsonResponse({'error': 'Missing ISBN.'}, status=400)

        isbn = re.sub(r'[^0-9A-Za-z]', '', isbn_raw).upper()
        found_book = None
        for book in Book.objects.all():
            db_isbn = re.sub(r'[^0-9A-Za-z]', '', (book.isbn or '')).upper()
            if db_isbn == isbn:
                found_book = book
                break

        if not found_book:
            return JsonResponse({'error': f'Book not found: {isbn_raw}'}, status=404)

        if not found_book.is_available():
            return JsonResponse({'error': f'{found_book.title} is unavailable.'}, status=400)

        if any(b['id'] == found_book.id for b in books):
            return JsonResponse({'error': 'Book already added.'}, status=400)

        books.append({
            'id': found_book.id,
            'title': found_book.title,
            'isbn': found_book.isbn,
            'author': found_book.author,
        })
        request.session['pos_books'] = books
        request.session.modified = True

        return JsonResponse({'books': books})

    # ✅ Manual Add
    if request.method == 'POST' and 'add_book' in request.POST:
        isbn_raw = request.POST.get('isbn', '').strip()
        isbn = re.sub(r'[^0-9A-Za-z]', '', isbn_raw).upper()
        found_book = None
        for book in Book.objects.all():
            db_isbn = re.sub(r'[^0-9A-Za-z]', '', (book.isbn or '')).upper()
            if db_isbn == isbn:
                found_book = book
                break

        if not found_book:
            messages.error(request, f'Book not found: {isbn_raw}')
        elif any(b['id'] == found_book.id for b in books):
            messages.warning(request, 'Book already added.')
        else:
            books.append({
                'id': found_book.id,
                'title': found_book.title,
                'isbn': found_book.isbn,
                'author': found_book.author
            })
            request.session['pos_books'] = books
            request.session.modified = True
            messages.success(request, f'Added: {found_book.title}')

        return render(request, 'library/pos_borrow_book.html', {
            'student': student,
            'books': books,
            'step': 'add_books'
        })

    # ✅ Continue and Confirm borrow
    if request.method == 'POST':
        if 'continue_borrow' in request.POST:
            return render(request, 'library/pos_borrow_book.html', {
                'student': student,
                'books': books,
                'step': 'confirm'
            })

        elif 'confirm_borrow' in request.POST:
            if not books:
                messages.error(request, 'No books selected.')
                return render(request, 'library/pos_borrow_book.html', {
                    'student': student,
                    'books': books,
                    'step': 'add_books'
                })

            transaction = Transaction.objects.create(
                student=student,
                transaction_code=Transaction.generate_transaction_code(),
                due_date=timezone.now() + timedelta(days=7),
                created_by=request.user
            )

            for b in books:
                book = Book.objects.get(id=b['id'])
                TransactionItem.objects.create(transaction=transaction, book=book)

            request.session.pop('pos_books', None)
            request.session.pop('pos_student_id', None)
            return redirect('pos_borrow_success', transaction_id=transaction.id)

    # ✅ Default render
    return render(request, 'library/pos_borrow_book.html', {
        'student': student,
        'books': request.session.get('pos_books', []),
        'step': 'add_books'
    })

@login_required
def pos_borrow_success(request, transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id)
    except Transaction.DoesNotExist:
        messages.error(request,'Transaction not found')
        return redirect('pos_home')
    return render(request,'library/pos_borrow_success.html',{'transaction':transaction,'student':transaction.student,'books':transaction.items.all()})

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Student

@csrf_exempt
def validate_student_id(request):
    # Only allow GET requests
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method."}, status=405)

    student_id = request.GET.get('student_id', '').strip()
    print("📥 Student ID received:", student_id)  # Debug output

    if not student_id:
        return JsonResponse({
            "valid": False,
            "approved": False,
            "reason": "Missing student ID."
        }, status=400)

    try:
        student = Student.objects.get(student_id=student_id)
        print("✅ Student found:", student)

        if getattr(student, "is_approved", False):
            # ✅ Save student in session so Django remembers them
            request.session['student_id'] = student_id
            print(f"💾 Session saved for student: {student_id}")

            return JsonResponse({
                "valid": True,
                "approved": True
            })
        else:
            return JsonResponse({
                "valid": True,
                "approved": False,
                "reason": "Magregister ka muna boiii!!."
            })
    except Student.DoesNotExist:
        return JsonResponse({
            "valid": False,
            "approved": False,
            "reason": "You are not registered. Please register first."
        })
    except Exception as e:
        print("❌ Unexpected error:", e)
        return JsonResponse({
            "valid": False,
            "approved": False,
            "reason": "Server error: " + str(e)
        }, status=500)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from library.models import Book

from django.http import JsonResponse
from .models import Book

def validate_book_isbn(request):
    isbn = request.GET.get('isbn', '').strip()
    normalized = ''.join(filter(str.isalnum, isbn)).upper()
    book = None

    try:
        book = Book.objects.get(isbn__iexact=isbn)
    except Book.DoesNotExist:
        for b in Book.objects.all():
            db_isbn = ''.join(filter(str.isalnum, b.isbn)).upper()
            if db_isbn == normalized:
                book = b
                break

    if book:
        return JsonResponse({
            'valid': True,
            'unavailable': not book.is_available(),
            'book': {'title': book.title}
        })
    return JsonResponse({'valid': False})

@login_required
def pos_return_book(request):
    if request.user.user_type != 'pos':
        return redirect('dashboard')
    
    student_id = request.GET.get('student_id') or request.session.get('pos_student_id')
    if not student_id:
        return redirect('pos_home')
    
    try:
        student = Student.objects.get(student_id=student_id, is_approved=True)
    except Student.DoesNotExist:
        messages.error(request, 'Student not found')
        return redirect('pos_home')
    
    if request.method == 'POST':
        if 'review_return' in request.POST:
            book_ids = request.POST.getlist('book_ids')
            if not book_ids:
                messages.error(request, 'Please select at least one book to return')
                borrowed_items = TransactionItem.objects.filter(
                    transaction__student=student,
                    status='borrowed',
                    transaction__approval_status='approved'
                ).select_related('book', 'transaction')
                return render(request, 'library/pos_return_book.html', {
                    'student': student,
                    'borrowed_items': borrowed_items,
                    'step': 'select_books'
                })
            
            selected_items = TransactionItem.objects.filter(
                id__in=book_ids,
                transaction__student=student,
                status='borrowed'
            ).select_related('book', 'transaction')
            
            return render(request, 'library/pos_return_book.html', {
                'student': student,
                'selected_items': selected_items,
                'step': 'confirm'
            })
        
        elif 'confirm_return' in request.POST:
            book_ids = request.POST.getlist('book_ids')
            if not book_ids:
                messages.error(request, 'No books selected for return')
                return redirect('pos_home')
            
            selected_items = TransactionItem.objects.filter(
                id__in=book_ids,
                transaction__student=student,
                status='borrowed'
            ).select_related('book', 'transaction')
            
            return_date = timezone.now()
            returned_items = []
            
            for item in selected_items:
                item.status = 'returned'
                item.return_date = return_date
                item.save()
                
                item.book.copies_available += 1
                item.book.save()
                returned_items.append(item)
                
                transaction = item.transaction
                all_returned = not transaction.items.filter(status='borrowed').exists()
                if all_returned:
                    transaction.status = 'returned'
                    transaction.return_date = return_date
                    transaction.save()
            
            still_borrowed_items = TransactionItem.objects.filter(
                transaction__student=student,
                status='borrowed',
                transaction__approval_status='approved'
            ).select_related('book', 'transaction')
            
            return render(request, 'library/pos_return_success.html', {
                'student': student,
                'returned_items': returned_items,
                'still_borrowed_items': still_borrowed_items,
                'return_date': return_date
            })
    
    borrowed_items = TransactionItem.objects.filter(
        transaction__student=student,
        status='borrowed',
        transaction__approval_status='approved'
    ).select_related('book', 'transaction')
    
    return render(request, 'library/pos_return_book.html', {
        'student': student,
        'borrowed_items': borrowed_items,
        'step': 'select_books'
    })
    
# views.py
from django.http import JsonResponse

def remove_borrow_book(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
    book_id = request.POST.get("book_id")
    if not book_id:
        return JsonResponse({"error": "Missing book ID"}, status=400)
    
    # Assuming your added books are stored in session as a list of dicts
    books = request.session.get("borrow_books", [])
    updated_books = [b for b in books if str(b.get("id")) != str(book_id)]
    
    request.session["borrow_books"] = updated_books
    request.session.modified = True

    return JsonResponse({"success": True, "books": updated_books})
