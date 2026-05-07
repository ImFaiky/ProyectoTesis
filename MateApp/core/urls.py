from django.urls import path
from . import views

urlpatterns = [
    # Main Dashboard
    path('', views.dashboard, name='dashboard'),
    path('discipline/<int:discipline_id>/', views.discipline_detail, name='discipline_detail'),
    path('play/<int:level_id>/', views.play_level_simulation, name='play_level'),
    
    # Student Progress
    path('my-progress/', views.my_progress, name='my_progress'),
    
    # Student Management
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_create, name='student_create'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),
    path('students/<int:pk>/profile/', views.student_profile, name='student_profile'),
    path('students/progress/<int:progress_id>/', views.student_level_detail, name='student_level_detail'),

    # Teacher Management (Admin only)
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/add/', views.teacher_create, name='teacher_create'),
    path('teachers/<int:pk>/edit/', views.teacher_edit, name='teacher_edit'),
    path('teachers/<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),

    # Discipline Management
    path('manage/disciplines/', views.DisciplineListView.as_view(), name='discipline_list'),
    path('manage/disciplines/add/', views.DisciplineCreateView.as_view(), name='discipline_add'),
    path('manage/disciplines/<int:pk>/edit/', views.DisciplineUpdateView.as_view(), name='discipline_edit'),
    path('manage/disciplines/<int:pk>/delete/', views.discipline_delete, name='discipline_delete'),
    path('manage/disciplines/<int:discipline_id>/analytics/', views.discipline_analytics, name='discipline_analytics'),
    
    # Level Management
    path('manage/disciplines/<int:discipline_id>/levels/', views.level_list, name='level_list'),
    path('manage/disciplines/<int:discipline_id>/levels/add/', views.LevelCreateView.as_view(), name='level_add'),
    path('manage/levels/<int:pk>/edit/', views.LevelUpdateView.as_view(), name='level_edit'),
    path('manage/levels/<int:pk>/delete/', views.level_delete, name='level_delete'),
    
    # Analytics
    path('analytics/', views.general_analytics, name='general_analytics'),

    # AJAX
    path('api/chart-data/', views.dashboard_chart_data, name='dashboard_chart_data'),
    path('api/upload-question-image/', views.upload_question_image, name='upload_question_image'),
    
    # Exports
    path('export/students/', views.export_students_csv, name='export_students'),
    path('export/disciplines/', views.export_disciplines_csv, name='export_disciplines'),
    path('export/scores/', views.export_scores_csv, name='export_scores'),

    # Classroom Management (Teachers)
    path('classrooms/', views.classroom_list, name='classroom_list'),
    path('classrooms/add/', views.classroom_create, name='classroom_create'),
    path('classrooms/<int:pk>/edit/', views.classroom_edit, name='classroom_edit'),
    path('classrooms/<int:pk>/delete/', views.classroom_delete, name='classroom_delete'),
    path('classrooms/<int:pk>/', views.classroom_detail, name='classroom_detail'),
    path('classrooms/<int:pk>/remove-student/<int:student_id>/', views.classroom_remove_student, name='classroom_remove_student'),

    # Student Enrollment
    path('join/', views.join_classroom, name='join_classroom'),
    path('my-classrooms/', views.my_classrooms, name='my_classrooms'),

    # AI (Gemini)
    path('ai/tutor/', views.ai_tutor_view, name='ai_tutor'),
    path('api/ai/chat/', views.ai_tutor_chat, name='ai_tutor_chat'),
    path('api/ai/generate-questions/', views.ai_generate_questions, name='ai_generate_questions'),
]
