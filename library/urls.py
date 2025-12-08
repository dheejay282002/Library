from django.urls import path
from . import views
from library.views import live_search_books, student_books

urlpatterns = [
    # Authentication & Verification
    path('', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('verify/', views.verify_student_id, name='verify_student_id'),
    path('verify_student/', views.verify_student, name='verify_student'),
    path('register/', views.student_registration, name='student_registration'),
    path('student-registration/', views.student_registration, name='student_registration'),
    path('verify-email/', views.verify_email, name='email_verification'),
    path('email-verification/', views.email_verification, name='email_verification'),
    path('resend-verification-code/', views.resend_verification_code, name='resend_verification_code'),

    # Admin student approvals
    path('admin/students/approve/<int:student_id>/', views.approve_student, name='approve_student'),
    path('admin/students/reject/<int:student_id>/', views.reject_student, name='reject_student'),
    path('reject-student/<int:student_id>/', views.reject_student, name='reject_student'),

    # Library status
    path('librarian/library-status/', views.library_status, name='library_status'),

    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('librarian/dashboard/', views.librarian_dashboard, name='librarian_dashboard'),

    # Student routes
    path('student/books/', student_books, name='student_books'),
    path('student/settings/', views.student_settings, name='student_settings'),
    path('student/books/live-search/', live_search_books, name='live_search_books'),

    # Admin routes
    path('admin/import-students/', views.import_students_csv, name='import_students_csv'),
    path('admin/import-books/', views.import_books_csv, name='import_books_csv'),
    path('admin/download-books-template/', views.download_books_csv_template, name='download_books_csv_template'),
    path('admin/download-students-template/', views.download_students_csv_template, name='download_students_csv_template'),
    path('admin/books/', views.manage_books, name='manage_books'),
    path('admin/books/add/', views.add_book, name='add_book'),
    path('admin/books/edit/<int:book_id>/', views.edit_book, name='edit_book'),
    path('admin/books/delete/<int:book_id>/', views.delete_book, name='delete_book'),
    path('admin/books/export/', views.export_books_by_category, name='export_books_by_category'),
    path('admin/students/', views.manage_students, name='manage_students'),
    path('admin/students/pending/', views.pending_students, name='pending_students'),
    path('admin/students/add/', views.add_student, name='add_student'),
    path('admin/students/edit/<int:student_id>/', views.edit_student, name='edit_student'),
    path('admin/students/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    path('admin/librarians/', views.manage_librarians, name='manage_librarians'),
    path('admin/librarians/add/', views.add_librarian, name='add_librarian'),
    path('admin/librarians/edit/<int:librarian_id>/', views.edit_librarian, name='edit_librarian'),
    path('admin/librarians/delete/<int:librarian_id>/', views.delete_librarian, name='delete_librarian'),
    path('admin/pos/', views.manage_pos, name='manage_pos'),
    path('admin/pos/add/', views.add_pos, name='add_pos'),
    path('admin/pos/edit/<int:pos_id>/', views.edit_pos, name='edit_pos'),
    path('admin/pos/delete/<int:pos_id>/', views.delete_pos, name='delete_pos'),
    path('admin/logs/', views.admin_logs, name='admin_logs'),
    path('admin/transactions/pending/', views.pending_transactions, name='pending_transactions'),
    path('admin/transactions/approve/<int:transaction_id>/', views.approve_transaction, name='approve_transaction'),
    path('admin/transactions/reject/<int:transaction_id>/', views.reject_transaction, name='reject_transaction'),
    path('admin/create-pos/', views.create_pos_account, name='create_pos_account'),
    path('admin/settings/', views.admin_settings, name='admin_settings'),

    # POS routes
    path('pos/home/', views.pos_home, name='pos_home'),
    path('pos/', views.pos_home, name='pos_home'),
   
    path('pos/', views.pos_home, name='pos_home'),
    path('pos/options/', views.pos_options, name='pos_options'),
    path('pos/borrow/', views.pos_borrow_book, name='pos_borrow_book'),
    path('pos/borrow/validate/', views.validate_book_isbn, name='validate_book_isbn'),
    path('pos/return/', views.pos_return_book, name='pos_return_book'),
    path('pos/remove-book/', views.remove_borrow_book, name='remove_borrow_book'),
    path('pos/borrow/success/<int:transaction_id>/', views.pos_borrow_success, name='pos_borrow_success'),
    path('pos/validate/', views.validate_student_id, name='validate_student_id'),
    path('validate_student_id/', views.validate_student_id, name='validate_student_id'),

    # Student book actions
    #path('books/', views.student_books, name='browse_books'),
    #path('add-to-cart/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
#    path('cart/', views.cart_view, name='cart'),
#   path('checkout/', views.checkout, name='checkout'),
#    path('orders/', views.student_orders, name='student_orders'),

    # Librarian orders
#    path('librarian/orders/', views.librarian_orders, name='librarian_orders'),
#    path('librarian/orders/update/<int:order_id>/<str:status>/', views.update_order_status, name='update_order_status'),
#   path('librarian/orders/new-count/', views.new_orders_count, name='new_orders_count'),
#    path('librarian/fetch-orders/', views.fetch_orders_librarian, name='fetch_orders_librarian'),

    # Cart & checkout
##    path('cart/update/', views.update_cart_ajax, name='update_cart_ajax'),
  ##  path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    ##path('gcash-payment/<int:order_id>/', views.gcash_payment, name='gcash_payment'),
    path('verify/', views.verify_student_id, name='verify_student_id'),
    path('ajax/check-student-id/', views.check_student_id_ajax, name='check_student_id_ajax'),

    path('ajax/send-reset-code/', views.ajax_send_reset_code, name='ajax_send_reset_code'),
    path('ajax/verify-reset-code/', views.ajax_verify_reset_code, name='ajax_verify_reset_code'),


]
