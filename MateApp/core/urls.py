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
    
    # Exports
    path('export/students/', views.export_students_csv, name='export_students'),
    path('export/disciplines/', views.export_disciplines_csv, name='export_disciplines'),
    path('export/scores/', views.export_scores_csv, name='export_scores'),
]
