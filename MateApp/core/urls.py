from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('discipline/<int:discipline_id>/', views.discipline_detail, name='discipline_detail'),
    path('play/<int:level_id>/', views.play_level_simulation, name='play_level'),
    
    # helper views
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_create, name='student_create'),
    path('students/progress/<int:progress_id>/', views.student_level_detail, name='student_level_detail'),

    # Management Views
    path('manage/disciplines/', views.DisciplineListView.as_view(), name='discipline_list'),
    path('manage/disciplines/add/', views.DisciplineCreateView.as_view(), name='discipline_add'),
    path('manage/disciplines/<int:pk>/edit/', views.DisciplineUpdateView.as_view(), name='discipline_edit'),
    
    path('manage/disciplines/<int:discipline_id>/levels/', views.level_list, name='level_list'),
    path('manage/disciplines/<int:discipline_id>/levels/add/', views.LevelCreateView.as_view(), name='level_add'),
    path('manage/levels/<int:pk>/edit/', views.LevelUpdateView.as_view(), name='level_edit'),
]
