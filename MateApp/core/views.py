from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models
from django.http import JsonResponse, HttpResponse
import json
import csv
import string
import random
from datetime import timedelta
from django.utils import timezone
from .models import Discipline, Level, UserLevelProgress, LevelAttempt, QuestionImage, AIConversation, Classroom, ClassroomEnrollment
from .services import save_level_progress
from .forms import DisciplineForm, LevelForm

from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

User = get_user_model()


def is_admin(user):
    return user.is_superuser

def is_management_user(user):
    return user.is_staff  # Both superusers and staff can manage

def is_student(user):
    return not user.is_staff and user.is_authenticated


def get_teacher_students(teacher):
    """Returns queryset of students enrolled in a teacher's classrooms."""
    student_ids = ClassroomEnrollment.objects.filter(
        classroom__teacher=teacher
    ).values_list('student_id', flat=True)
    return User.objects.filter(id__in=student_ids)

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_admin(self.request.user)

class ManagementRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_management_user(self.request.user)

# --- Discipline Views ---
class DisciplineListView(LoginRequiredMixin, ManagementRequiredMixin, ListView):
    model = Discipline
    template_name = 'core/discipline_list.html'
    context_object_name = 'disciplines'
    paginate_by = 10

    def get_queryset(self):
        if is_admin(self.request.user):
            return Discipline.objects.all().order_by('name')
        return Discipline.objects.filter(created_by=self.request.user).order_by('name')

class DisciplineCreateView(LoginRequiredMixin, ManagementRequiredMixin, CreateView):
    model = Discipline
    form_class = DisciplineForm
    template_name = 'core/discipline_form.html'
    success_url = reverse_lazy('discipline_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Discipline created successfully.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Error creating discipline. Please check the form.')
        return super().form_invalid(form)

class DisciplineUpdateView(LoginRequiredMixin, ManagementRequiredMixin, UpdateView):
    model = Discipline
    form_class = DisciplineForm
    template_name = 'core/discipline_form.html'
    success_url = reverse_lazy('discipline_list')

    def get_queryset(self):
        if is_admin(self.request.user):
            return Discipline.objects.all()
        return Discipline.objects.filter(created_by=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Discipline updated successfully.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Error updating discipline. Please check the form.')
        return super().form_invalid(form)

# --- Level Views ---
@login_required
@user_passes_test(is_management_user)
def level_list(request, discipline_id):
    if is_admin(request.user):
        discipline = get_object_or_404(Discipline, id=discipline_id)
    else:
        discipline = get_object_or_404(Discipline, id=discipline_id, created_by=request.user)
    levels_qs = discipline.levels.all().order_by('number')
    
    paginator = Paginator(levels_qs, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/level_list.html', {'discipline': discipline, 'levels': page_obj})

class LevelCreateView(LoginRequiredMixin, ManagementRequiredMixin, CreateView):
    model = Level
    form_class = LevelForm
    template_name = 'core/level_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if is_admin(self.request.user):
            kwargs['discipline'] = get_object_or_404(Discipline, id=self.kwargs.get('discipline_id'))
        else:
            kwargs['discipline'] = get_object_or_404(Discipline, id=self.kwargs.get('discipline_id'), created_by=self.request.user)
        return kwargs

    def form_valid(self, form):
        form.instance.discipline_id = self.kwargs.get('discipline_id')
        response = super().form_valid(form)
        student_ids = self.request.POST.getlist('assigned_students')
        self.object.assigned_students.set(student_ids)
        messages.success(self.request, 'Level created successfully.')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Error creating level. Please check the form.')
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('level_list', kwargs={'discipline_id': self.kwargs['discipline_id']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if is_admin(self.request.user):
            context['discipline'] = get_object_or_404(Discipline, id=self.kwargs.get('discipline_id'))
            context['all_students'] = User.objects.filter(is_superuser=False, is_staff=False).order_by('username')
        else:
            context['discipline'] = get_object_or_404(Discipline, id=self.kwargs.get('discipline_id'), created_by=self.request.user)
            context['all_students'] = get_teacher_students(self.request.user).order_by('username')
        context['assigned_student_ids'] = []
        return context

class LevelUpdateView(LoginRequiredMixin, ManagementRequiredMixin, UpdateView):
    model = Level
    form_class = LevelForm
    template_name = 'core/level_form.html'

    def get_success_url(self):
        return reverse_lazy('level_list', kwargs={'discipline_id': self.object.discipline.id})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        student_ids = self.request.POST.getlist('assigned_students')
        self.object.assigned_students.set(student_ids)
        messages.success(self.request, 'Level updated successfully.')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Error updating level. Please check the form.')
        return super().form_invalid(form)

    def get_queryset(self):
        if is_admin(self.request.user):
            return Level.objects.all()
        return Level.objects.filter(discipline__created_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['discipline'] = self.object.discipline
        if is_admin(self.request.user):
            context['all_students'] = User.objects.filter(is_superuser=False, is_staff=False).order_by('username')
        else:
            context['all_students'] = get_teacher_students(self.request.user).order_by('username')
        context['assigned_student_ids'] = list(self.object.assigned_students.values_list('id', flat=True))
        return context

@login_required
@user_passes_test(is_management_user)
def discipline_delete(request, discipline_id):
    if is_admin(request.user):
        discipline = get_object_or_404(Discipline, id=discipline_id)
    else:
        discipline = get_object_or_404(Discipline, id=discipline_id, created_by=request.user)
    
    if request.method == 'POST':
        try:
            discipline_name = discipline.name
            discipline.delete()
            messages.success(request, f'Discipline "{discipline_name}" deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting discipline: {e}')
        
        return redirect('discipline_list')
    
    return render(request, 'core/discipline_confirm_delete.html', {'discipline': discipline})

@login_required
@user_passes_test(is_management_user)
def level_delete(request, level_id):
    if is_admin(request.user):
        level = get_object_or_404(Level, id=level_id)
    else:
        level = get_object_or_404(Level, id=level_id, discipline__created_by=request.user)
    discipline_id = level.discipline.id
    
    if request.method == 'POST':
        try:
            level_name = level.name
            level.delete()
            messages.success(request, f'Level "{level_name}" deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting level: {e}')
        
        return redirect('level_list', discipline_id=discipline_id)
    
    return render(request, 'core/level_confirm_delete.html', {'level': level})


# --- Existing Views ---

@login_required
def dashboard(request):
    if is_management_user(request.user):
        # Admin sees ALL students; Teacher sees only THEIR enrolled students
        if is_admin(request.user):
            students = User.objects.filter(is_superuser=False, is_staff=False).order_by('-total_points')
        else:
            students = get_teacher_students(request.user).order_by('-total_points')

        student_count = students.count()
        if is_admin(request.user):
            discipline_count = Discipline.objects.count()
            level_count = Level.objects.count()
        else:
            discipline_count = Discipline.objects.filter(created_by=request.user).count()
            level_count = Level.objects.filter(discipline__created_by=request.user).count()
        recent_progress = UserLevelProgress.objects.filter(user__in=students).select_related('user', 'level').order_by('-completed_at')[:10]
        
        # Student Progress Summary
        student_progress_data = []
        for student in students:
            progress_records = UserLevelProgress.objects.filter(user=student)
            total_levels_completed = progress_records.count()
            total_stars = progress_records.aggregate(models.Sum('stars'))['stars__sum'] or 0
            avg_score = progress_records.aggregate(models.Avg('score'))['score__avg'] or 0
            
            student_progress_data.append({
                'student': student,
                'levels_completed': total_levels_completed,
                'total_stars': total_stars,
                'avg_score': round(avg_score, 1),
                'last_activity': progress_records.order_by('-completed_at').first().completed_at if progress_records.exists() else None
            })
        
        # Discipline Performance Summary (filtered by teacher's students and disciplines)
        discipline_performance = []
        disc_qs = Discipline.objects.all() if is_admin(request.user) else Discipline.objects.filter(created_by=request.user)
        for discipline in disc_qs:
            total_progress = UserLevelProgress.objects.filter(level__discipline=discipline, user__in=students)
            discipline_performance.append({
                'discipline': discipline,
                'total_attempts': total_progress.count(),
                'unique_students': total_progress.values('user').distinct().count(),
                'avg_stars': total_progress.aggregate(models.Avg('stars'))['stars__avg'] or 0,
                'avg_score': total_progress.aggregate(models.Avg('score'))['score__avg'] or 0
            })
        
        # Overall Avg Score (filtered)
        overall_avg_score = UserLevelProgress.objects.filter(user__in=students).aggregate(models.Avg('score'))['score__avg'] or 0
        
        # Top Performers
        top_students = students[:5]

        # Teacher's classrooms
        classrooms = Classroom.objects.filter(teacher=request.user) if not is_admin(request.user) else None
        
        # Serialize data for JavaScript
        student_progress_json = json.dumps([
            {
                'student': {
                    'username': data['student'].username,
                    'total_points': data['student'].total_points
                },
                'levels_completed': data['levels_completed'],
                'total_stars': data['total_stars'],
                'avg_score': data['avg_score']
            }
            for data in student_progress_data[:10]
        ])
        
        discipline_performance_json = json.dumps([
            {
                'discipline': {
                    'name': perf['discipline'].name
                },
                'avg_score': perf['avg_score'],
                'avg_stars': perf['avg_stars']
            }
            for perf in discipline_performance
        ])
        
        return render(request, 'core/admin_dashboard.html', {
            'student_count': student_count,
            'discipline_count': discipline_count,
            'level_count': level_count,
            'recent_progress': recent_progress,
            'student_progress_data': student_progress_data,
            'discipline_performance': discipline_performance,
            'top_students': top_students,
            'student_progress_json': student_progress_json,
            'discipline_performance_json': discipline_performance_json,
            'overall_avg_score': round(overall_avg_score, 1),
            'classrooms': classrooms,
            'is_admin_user': is_admin(request.user),
        })
    else:
        # Student Dashboard Logic: show enrolled classrooms with their disciplines
        enrollments = ClassroomEnrollment.objects.filter(
            student=request.user
        ).select_related('classroom__teacher').prefetch_related('classroom__disciplines')

        classrooms_data = []
        for enrollment in enrollments:
            cr = enrollment.classroom
            if not cr.is_active:
                continue
            disciplines = cr.disciplines.filter(is_active=True)
            classrooms_data.append({
                'classroom': cr,
                'disciplines': disciplines,
            })

        return render(request, 'core/dashboard.html', {
            'classrooms_data': classrooms_data,
        })

@login_required
def discipline_detail(request, discipline_id):
    discipline = get_object_or_404(Discipline, id=discipline_id)
    levels = discipline.levels.filter(is_active=True).order_by('number')
    if is_student(request.user):
        levels = levels.filter(assigned_students=request.user)
    
    levels_data = []
    for level in levels:
        progress = UserLevelProgress.objects.filter(user=request.user, level=level).first()
        levels_data.append({
            'level': level,
            'progress': progress
        })

    return render(request, 'core/discipline_detail.html', {
        'discipline': discipline,
        'levels_data': levels_data
    })

@login_required
def play_level_simulation(request, level_id):
    level = get_object_or_404(Level, id=level_id)

    if request.method == 'POST':
        if not is_student(request.user) and not request.user.is_superuser: # Allow superuser to test too
             messages.error(request, "Only students can save progress.")
             return redirect('dashboard')

        score = int(request.POST.get('score', 0))
        stars = int(request.POST.get('stars', 0))
        time_seconds = int(request.POST.get('time_seconds', 0))
        answers_json = request.POST.get('answers', '[]')
        
        try:
            answers = json.loads(answers_json)
        except json.JSONDecodeError:
            answers = []

        # Save level progress
        progress = save_level_progress(request.user, level, score, stars, answers, time_seconds)
        
        messages.success(request, f'Level "{level.discipline.name} - Level {level.number}" completed! Score: {score}, Stars: {stars}')
        
        return redirect('discipline_detail', discipline_id=level.discipline.id)
    
    return render(request, 'core/play_level.html', {'level': level})

@login_required
@user_passes_test(is_management_user)
def student_list(request):
    if is_admin(request.user):
        students_qs = User.objects.filter(is_superuser=False, is_staff=False).order_by('username')
    else:
        students_qs = get_teacher_students(request.user).order_by('username')
    paginator = Paginator(students_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/student_list.html', {'students': page_obj})

@login_required
@user_passes_test(is_management_user)
def student_create(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST.get('email')
        password = request.POST['password']
        
        try:
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, 'Student created successfully.')
            return redirect('student_list')
        except Exception as e:
            messages.error(request, f'Error creating student: {e}')
            
    return render(request, 'core/student_form.html')

@login_required
@user_passes_test(is_management_user)
def student_edit(request, pk):
    student = get_object_or_404(User, pk=pk, is_superuser=False, is_staff=False)
    
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            student.username = username
            if email:
                student.email = email
            if password:
                student.set_password(password)
            student.save()
            messages.success(request, 'Student updated successfully.')
            return redirect('student_list')
        except Exception as e:
            messages.error(request, f'Error updating student: {e}')
    
    return render(request, 'core/student_form.html', {'student': student})

@login_required
@user_passes_test(is_management_user)
def student_delete(request, pk):
    student = get_object_or_404(User, pk=pk, is_superuser=False, is_staff=False)
    
    if request.method == 'POST':
        try:
            student_name = student.username
            student.delete()
            messages.success(request, f'Student "{student_name}" deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting student: {e}')
        
        return redirect('student_list')
    
    return render(request, 'core/student_confirm_delete.html', {'student': student})


# ============================================
# Teacher CRUD (Admin only)
# ============================================

@login_required
@user_passes_test(is_admin)
def teacher_list(request):
    teachers = User.objects.filter(is_staff=True, is_superuser=False).order_by('username')
    return render(request, 'core/teacher_list.html', {'teachers': teachers})


@login_required
@user_passes_test(is_admin)
def teacher_create(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'core/teacher_form.html')

        try:
            teacher = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            teacher.is_staff = True
            teacher.save()
            messages.success(request, f'Teacher "{username}" created successfully.')
            return redirect('teacher_list')
        except Exception as e:
            messages.error(request, f'Error creating teacher: {e}')

    return render(request, 'core/teacher_form.html')


@login_required
@user_passes_test(is_admin)
def teacher_edit(request, pk):
    teacher = get_object_or_404(User, pk=pk, is_staff=True, is_superuser=False)

    if request.method == 'POST':
        teacher.username = request.POST.get('username', '').strip() or teacher.username
        teacher.first_name = request.POST.get('first_name', '').strip()
        teacher.last_name = request.POST.get('last_name', '').strip()
        teacher.email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        if password:
            teacher.set_password(password)
        try:
            teacher.save()
            messages.success(request, f'Teacher "{teacher.username}" updated successfully.')
            return redirect('teacher_list')
        except Exception as e:
            messages.error(request, f'Error updating teacher: {e}')

    return render(request, 'core/teacher_form.html', {'teacher': teacher})


@login_required
@user_passes_test(is_admin)
def teacher_delete(request, pk):
    teacher = get_object_or_404(User, pk=pk, is_staff=True, is_superuser=False)

    if request.method == 'POST':
        name = teacher.username
        teacher.delete()
        messages.success(request, f'Teacher "{name}" deleted successfully.')
        return redirect('teacher_list')

    return render(request, 'core/teacher_confirm_delete.html', {'teacher': teacher})


@login_required
@user_passes_test(is_student)
def my_progress(request):
    # Get all progress records for the current student
    progress_records = UserLevelProgress.objects.filter(user=request.user).select_related('level', 'level__discipline').order_by('-completed_at')
    
    # Group progress by discipline
    disciplines_progress = {}
    for progress in progress_records:
        discipline = progress.level.discipline
        if discipline not in disciplines_progress:
            disciplines_progress[discipline] = {
                'discipline': discipline,
                'total_levels': discipline.levels.filter(is_active=True).count(),
                'completed_levels': 0,
                'total_stars': 0,
                'total_score': 0,
                'avg_score': 0,
                'progress_records': []
            }
        
        disciplines_progress[discipline]['completed_levels'] += 1
        disciplines_progress[discipline]['total_stars'] += progress.stars or 0
        disciplines_progress[discipline]['total_score'] += progress.score or 0
        disciplines_progress[discipline]['progress_records'].append(progress)
    
    # Calculate averages and percentages
    for discipline_data in disciplines_progress.values():
        if discipline_data['completed_levels'] > 0:
            discipline_data['avg_score'] = discipline_data['total_score'] / discipline_data['completed_levels']
            discipline_data['completion_percentage'] = (discipline_data['completed_levels'] / discipline_data['total_levels']) * 100 if discipline_data['total_levels'] > 0 else 0
        else:
            discipline_data['completion_percentage'] = 0
    
    # Get overall statistics
    total_completed_levels = sum(data['completed_levels'] for data in disciplines_progress.values())
    total_possible_levels = sum(data['total_levels'] for data in disciplines_progress.values())
    overall_completion = (total_completed_levels / total_possible_levels * 100) if total_possible_levels > 0 else 0
    
    # Get recent activity (last 10)
    recent_activity = progress_records[:10]
    
    return render(request, 'core/my_progress.html', {
        'disciplines_progress': disciplines_progress.values(),
        'overall_completion': overall_completion,
        'total_completed_levels': total_completed_levels,
        'total_possible_levels': total_possible_levels,
        'recent_activity': recent_activity,
        'total_points': request.user.total_points
    })

@login_required
@user_passes_test(is_management_user)
def student_level_detail(request, progress_id):
    progress = get_object_or_404(UserLevelProgress, id=progress_id)
    return render(request, 'core/student_level_detail.html', {'progress': progress})

@login_required
@user_passes_test(is_management_user)
def student_profile(request, pk):
    student = get_object_or_404(User, pk=pk, is_superuser=False, is_staff=False)
    
    # Get all progress records
    progress_records = UserLevelProgress.objects.filter(
        user=student
    ).select_related('level', 'level__discipline').order_by('-completed_at')
    
    # Group progress by discipline
    disciplines_progress = {}
    for record in progress_records:
        disc_name = record.level.discipline.name
        if disc_name not in disciplines_progress:
            disciplines_progress[disc_name] = {
                'discipline': record.level.discipline,
                'records': [],
                'total_score': 0,
                'total_stars': 0,
                'count': 0,
            }
        disciplines_progress[disc_name]['records'].append(record)
        disciplines_progress[disc_name]['total_score'] += record.score
        disciplines_progress[disc_name]['total_stars'] += record.stars
        disciplines_progress[disc_name]['count'] += 1
    
    # Calculate averages
    for disc_name, data in disciplines_progress.items():
        data['avg_score'] = round(data['total_score'] / data['count'], 1) if data['count'] > 0 else 0
    
    # Stats
    total_levels_completed = progress_records.count()
    total_stars = sum(r.stars for r in progress_records)
    avg_score = round(sum(r.score for r in progress_records) / total_levels_completed, 1) if total_levels_completed > 0 else 0
    recent_activity = progress_records[:10]
    
    # LevelAttempt history for this student
    all_attempts = LevelAttempt.objects.filter(
        user=student
    ).select_related('level', 'level__discipline').order_by('created_at')
    
    # Per-level attempt & time data for charts
    level_attempt_data = []
    for record in progress_records:
        level_attempts = all_attempts.filter(level=record.level)
        avg_time = level_attempts.aggregate(models.Avg('time_seconds'))['time_seconds__avg'] or 0
        level_attempt_data.append({
            'level_label': f"{record.level.discipline.name} - Lvl {record.level.number}",
            'attempts': record.attempts,
            'best_time': record.best_time_seconds or 0,
            'avg_time': round(avg_time),
            'best_score': record.score,
        })
    
    # Attempt history timeline (score & time evolution)
    attempt_history = [{
        'date': a.created_at.strftime('%Y-%m-%d %H:%M'),
        'level_label': f"{a.level.discipline.name} - Lvl {a.level.number}",
        'score': a.score,
        'time_seconds': a.time_seconds,
        'stars': a.stars,
    } for a in all_attempts]
    
    level_attempt_json = json.dumps(level_attempt_data)
    attempt_history_json = json.dumps(attempt_history)
    total_attempts = all_attempts.count()
    avg_time = round(all_attempts.aggregate(models.Avg('time_seconds'))['time_seconds__avg'] or 0)
    
    return render(request, 'core/student_profile.html', {
        'student': student,
        'disciplines_progress': disciplines_progress.values(),
        'total_levels_completed': total_levels_completed,
        'total_stars': total_stars,
        'avg_score': avg_score,
        'recent_activity': recent_activity,
        'total_attempts': total_attempts,
        'avg_time': avg_time,
        'level_attempt_json': level_attempt_json,
        'attempt_history_json': attempt_history_json,
    })

@login_required
@user_passes_test(is_management_user)
def discipline_analytics(request, discipline_id):
    if is_admin(request.user):
        discipline = get_object_or_404(Discipline, id=discipline_id)
    else:
        discipline = get_object_or_404(Discipline, id=discipline_id, created_by=request.user)
    levels = Level.objects.filter(discipline=discipline).order_by('number')
    
    # All progress for this discipline
    all_progress = UserLevelProgress.objects.filter(
        level__discipline=discipline
    ).select_related('user', 'level')
    
    # General stats
    total_attempts = all_progress.count()
    unique_students = all_progress.values('user').distinct().count()
    avg_score = all_progress.aggregate(models.Avg('score'))['score__avg'] or 0
    avg_stars = all_progress.aggregate(models.Avg('stars'))['stars__avg'] or 0
    
    # Per-level stats
    level_stats = []
    for level in levels:
        level_progress = all_progress.filter(level=level)
        level_stats.append({
            'level': level,
            'attempts': level_progress.count(),
            'avg_score': round(level_progress.aggregate(models.Avg('score'))['score__avg'] or 0, 1),
            'avg_stars': round(level_progress.aggregate(models.Avg('stars'))['stars__avg'] or 0, 1),
            'max_score': level_progress.aggregate(models.Max('score'))['score__max'] or 0,
            'students': level_progress.values('user').distinct().count(),
        })
    
    # Per-student performance in this discipline
    students_in_discipline = []
    student_ids = all_progress.values_list('user', flat=True).distinct()
    for student_id in student_ids:
        student = User.objects.get(pk=student_id)
        student_progress = all_progress.filter(user=student)
        students_in_discipline.append({
            'student': student,
            'levels_completed': student_progress.count(),
            'avg_score': round(student_progress.aggregate(models.Avg('score'))['score__avg'] or 0, 1),
            'total_stars': student_progress.aggregate(models.Sum('stars'))['stars__sum'] or 0,
            'last_activity': student_progress.order_by('-completed_at').first().completed_at if student_progress.exists() else None,
        })
    students_in_discipline.sort(key=lambda x: x['avg_score'], reverse=True)
    
    # JSON for charts
    level_stats_json = json.dumps([{
        'level_number': s['level'].number,
        'attempts': s['attempts'],
        'avg_score': s['avg_score'],
        'avg_stars': s['avg_stars'],
        'students': s['students'],
    } for s in level_stats])
    
    return render(request, 'core/discipline_analytics.html', {
        'discipline': discipline,
        'total_attempts': total_attempts,
        'unique_students': unique_students,
        'avg_score': round(avg_score, 1),
        'avg_stars': round(avg_stars, 1),
        'level_stats': level_stats,
        'students_in_discipline': students_in_discipline,
        'level_stats_json': level_stats_json,
        'total_levels': levels.count(),
    })

@login_required
@user_passes_test(is_management_user)
def export_students_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students_progress.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Username', 'Email', 'Total Points', 'Current Level', 'Levels Completed', 'Total Stars', 'Avg Score', 'Last Activity'])
    
    students = User.objects.filter(is_superuser=False, is_staff=False).order_by('-total_points')
    for student in students:
        progress = UserLevelProgress.objects.filter(user=student)
        levels_completed = progress.count()
        total_stars = progress.aggregate(models.Sum('stars'))['stars__sum'] or 0
        avg_score = progress.aggregate(models.Avg('score'))['score__avg'] or 0
        last_activity = progress.order_by('-completed_at').first()
        last_date = last_activity.completed_at.strftime('%Y-%m-%d %H:%M') if last_activity else 'N/A'
        
        writer.writerow([
            student.username,
            student.email or 'N/A',
            student.total_points,
            student.current_level,
            levels_completed,
            total_stars,
            round(avg_score, 1),
            last_date,
        ])
    
    return response

@login_required
@user_passes_test(is_management_user)
def export_disciplines_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="disciplines_performance.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Discipline', 'Total Attempts', 'Unique Students', 'Avg Stars', 'Avg Score'])
    
    for discipline in Discipline.objects.all():
        progress = UserLevelProgress.objects.filter(level__discipline=discipline)
        writer.writerow([
            discipline.name,
            progress.count(),
            progress.values('user').distinct().count(),
            round(progress.aggregate(models.Avg('stars'))['stars__avg'] or 0, 1),
            round(progress.aggregate(models.Avg('score'))['score__avg'] or 0, 1),
        ])
    
    return response

@login_required
@user_passes_test(is_management_user)
def export_scores_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="scores_detail.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student', 'Discipline', 'Level', 'Score', 'Stars', 'Completed At'])
    
    records = UserLevelProgress.objects.all().select_related('user', 'level', 'level__discipline').order_by('-completed_at')
    for r in records:
        writer.writerow([
            r.user.username,
            r.level.discipline.name,
            r.level.number,
            r.score,
            r.stars,
            r.completed_at.strftime('%Y-%m-%d %H:%M'),
        ])
    
    return response

@login_required
@user_passes_test(is_management_user)
def dashboard_chart_data(request):
    period = request.GET.get('period', 'all')
    now = timezone.now()
    
    if period == 'today':
        date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        date_from = now - timedelta(days=7)
    elif period == 'month':
        date_from = now - timedelta(days=30)
    else:
        date_from = None
    
    # Determine student scope
    if is_admin(request.user):
        students = User.objects.filter(is_superuser=False, is_staff=False)
    else:
        students = get_teacher_students(request.user)

    # Filter progress by date and student scope
    progress_qs = UserLevelProgress.objects.filter(user__in=students)
    if date_from:
        progress_qs = progress_qs.filter(completed_at__gte=date_from)
    student_data = []
    for student in students:
        student_progress = progress_qs.filter(user=student)
        if student_progress.exists():
            student_data.append({
                'username': student.username,
                'total_points': student_progress.aggregate(models.Sum('score'))['score__sum'] or 0,
                'total_stars': student_progress.aggregate(models.Sum('stars'))['stars__sum'] or 0,
                'avg_score': round(student_progress.aggregate(models.Avg('score'))['score__avg'] or 0, 1),
                'levels_completed': student_progress.count(),
            })
    student_data.sort(key=lambda x: x['total_points'], reverse=True)
    student_data = student_data[:10]
    
    # Discipline data (filtered by ownership)
    discipline_data = []
    disc_qs = Discipline.objects.all() if is_admin(request.user) else Discipline.objects.filter(created_by=request.user)
    for discipline in disc_qs:
        disc_progress = progress_qs.filter(level__discipline=discipline)
        if disc_progress.exists() or date_from is None:
            discipline_data.append({
                'name': discipline.name,
                'avg_score': round(disc_progress.aggregate(models.Avg('score'))['score__avg'] or 0, 1),
                'avg_stars': round(disc_progress.aggregate(models.Avg('stars'))['stars__avg'] or 0, 1),
            })
    
    return JsonResponse({
        'student_data': student_data,
        'discipline_data': discipline_data,
        'period': period,
    })


@login_required
@user_passes_test(is_management_user)
def general_analytics(request):
    """General analytics: attempts and time per level. Teacher sees only their students."""
    # Determine student scope
    if is_admin(request.user):
        students = User.objects.filter(is_superuser=False, is_staff=False)
    else:
        students = get_teacher_students(request.user)

    if is_admin(request.user):
        disciplines = Discipline.objects.filter(is_active=True).prefetch_related('levels')
    else:
        disciplines = Discipline.objects.filter(is_active=True, created_by=request.user).prefetch_related('levels')
    
    # Build per-level stats from LevelAttempt (filtered by students)
    level_stats = []
    for discipline in disciplines:
        for level in discipline.levels.filter(is_active=True).order_by('number'):
            attempts = LevelAttempt.objects.filter(level=level, user__in=students)
            attempt_count = attempts.count()
            if attempt_count == 0:
                continue
            avg_time = attempts.aggregate(models.Avg('time_seconds'))['time_seconds__avg'] or 0
            avg_score = attempts.aggregate(models.Avg('score'))['score__avg'] or 0
            min_time = attempts.aggregate(models.Min('time_seconds'))['time_seconds__min'] or 0
            max_time = attempts.aggregate(models.Max('time_seconds'))['time_seconds__max'] or 0
            unique_students = attempts.values('user').distinct().count()
            
            # Average attempts per student for this level
            progress_records = UserLevelProgress.objects.filter(level=level, user__in=students)
            avg_attempts = progress_records.aggregate(models.Avg('attempts'))['attempts__avg'] or 0
            
            level_stats.append({
                'discipline_name': discipline.name,
                'level_number': level.number,
                'level_label': f"{discipline.name} - Lvl {level.number}",
                'total_attempts': attempt_count,
                'avg_attempts_per_student': round(avg_attempts, 1),
                'unique_students': unique_students,
                'avg_time': round(avg_time),
                'min_time': min_time,
                'max_time': max_time,
                'avg_score': round(avg_score, 1),
            })
    
    # Per-student summary (filtered)
    student_stats = []
    for student in students:
        attempts = LevelAttempt.objects.filter(user=student)
        if not attempts.exists():
            continue
        progress = UserLevelProgress.objects.filter(user=student)
        total_attempts = attempts.count()
        avg_time = attempts.aggregate(models.Avg('time_seconds'))['time_seconds__avg'] or 0
        avg_score = attempts.aggregate(models.Avg('score'))['score__avg'] or 0
        levels_played = progress.count()
        avg_attempts_per_level = round(total_attempts / levels_played, 1) if levels_played > 0 else 0
        
        student_stats.append({
            'student': student,
            'total_attempts': total_attempts,
            'levels_played': levels_played,
            'avg_attempts_per_level': avg_attempts_per_level,
            'avg_time': round(avg_time),
            'avg_score': round(avg_score, 1),
        })
    student_stats.sort(key=lambda x: x['total_attempts'], reverse=True)
    
    # JSON for charts
    level_stats_json = json.dumps(level_stats)
    student_stats_json = json.dumps([{
        'username': s['student'].username,
        'total_attempts': s['total_attempts'],
        'avg_attempts_per_level': s['avg_attempts_per_level'],
        'avg_time': s['avg_time'],
        'avg_score': s['avg_score'],
    } for s in student_stats])
    
    return render(request, 'core/general_analytics.html', {
        'level_stats': level_stats,
        'student_stats': student_stats,
        'level_stats_json': level_stats_json,
        'student_stats_json': student_stats_json,
    })


@login_required
@require_POST
@user_passes_test(is_management_user)
def upload_question_image(request):
    image_file = request.FILES.get('image')
    if not image_file:
        return JsonResponse({'error': 'No image provided'}, status=400)

    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if image_file.content_type not in allowed_types:
        return JsonResponse({'error': 'Invalid file type. Use JPG, PNG, GIF or WEBP.'}, status=400)

    if image_file.size > 5 * 1024 * 1024:
        return JsonResponse({'error': 'Image too large. Max 5MB.'}, status=400)

    qi = QuestionImage(image=image_file)
    qi.save()

    return JsonResponse({'url': qi.image.url, 'id': qi.id})


# ============================================
# Classroom Management Views
# ============================================

def generate_classroom_code(length=6):
    """Generate a unique classroom code."""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        if not Classroom.objects.filter(code=code).exists():
            return code


@login_required
@user_passes_test(is_management_user)
def classroom_list(request):
    """List classrooms. Admin sees all; teacher sees own."""
    if is_admin(request.user):
        classrooms = Classroom.objects.select_related('teacher').all()
    else:
        classrooms = Classroom.objects.filter(teacher=request.user)
    return render(request, 'core/classroom_list.html', {
        'classrooms': classrooms,
        'is_admin_user': is_admin(request.user),
    })


@login_required
@user_passes_test(is_management_user)
def classroom_create(request):
    """Create a new classroom."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        access_password = request.POST.get('access_password', '').strip()

        if not name or not access_password:
            messages.error(request, 'Name and access password are required.')
            return render(request, 'core/classroom_form.html', {
                'all_disciplines': Discipline.objects.filter(is_active=True, created_by=request.user) if not is_admin(request.user) else Discipline.objects.filter(is_active=True),
            })

        classroom = Classroom.objects.create(
            teacher=request.user,
            name=name,
            code=generate_classroom_code(),
            access_password=access_password,
            description=description,
        )
        discipline_ids = request.POST.getlist('disciplines')
        if discipline_ids:
            classroom.disciplines.set(discipline_ids)
        messages.success(request, f'Classroom "{classroom.name}" created. Code: {classroom.code}')
        return redirect('classroom_list')

    return render(request, 'core/classroom_form.html', {
        'all_disciplines': Discipline.objects.filter(is_active=True, created_by=request.user) if not is_admin(request.user) else Discipline.objects.filter(is_active=True),
    })


@login_required
@user_passes_test(is_management_user)
def classroom_edit(request, pk):
    """Edit an existing classroom."""
    classroom = get_object_or_404(Classroom, pk=pk)
    # Only the owner teacher or admin can edit
    if not is_admin(request.user) and classroom.teacher != request.user:
        messages.error(request, 'You do not have permission to edit this classroom.')
        return redirect('classroom_list')

    if request.method == 'POST':
        classroom.name = request.POST.get('name', '').strip() or classroom.name
        classroom.description = request.POST.get('description', '').strip()
        new_password = request.POST.get('access_password', '').strip()
        if new_password:
            classroom.access_password = new_password
        classroom.is_active = request.POST.get('is_active') == 'on'
        classroom.save()
        discipline_ids = request.POST.getlist('disciplines')
        classroom.disciplines.set(discipline_ids)
        messages.success(request, f'Classroom "{classroom.name}" updated successfully.')
        return redirect('classroom_list')

    return render(request, 'core/classroom_form.html', {
        'classroom': classroom,
        'all_disciplines': Discipline.objects.filter(is_active=True, created_by=request.user) if not is_admin(request.user) else Discipline.objects.filter(is_active=True),
        'selected_discipline_ids': list(classroom.disciplines.values_list('id', flat=True)),
    })


@login_required
@user_passes_test(is_management_user)
def classroom_delete(request, pk):
    """Delete a classroom."""
    classroom = get_object_or_404(Classroom, pk=pk)
    if not is_admin(request.user) and classroom.teacher != request.user:
        messages.error(request, 'You do not have permission to delete this classroom.')
        return redirect('classroom_list')

    if request.method == 'POST':
        name = classroom.name
        classroom.delete()
        messages.success(request, f'Classroom "{name}" deleted successfully.')
        return redirect('classroom_list')

    return render(request, 'core/classroom_confirm_delete.html', {'classroom': classroom})


@login_required
@user_passes_test(is_management_user)
def classroom_detail(request, pk):
    """View classroom detail with enrolled students."""
    classroom = get_object_or_404(Classroom, pk=pk)
    if not is_admin(request.user) and classroom.teacher != request.user:
        messages.error(request, 'You do not have permission to view this classroom.')
        return redirect('classroom_list')

    enrollments = classroom.enrollments.select_related('student').order_by('-enrolled_at')
    return render(request, 'core/classroom_detail.html', {
        'classroom': classroom,
        'enrollments': enrollments,
    })


@login_required
@user_passes_test(is_management_user)
def classroom_remove_student(request, pk, student_id):
    """Remove a student from a classroom."""
    classroom = get_object_or_404(Classroom, pk=pk)
    if not is_admin(request.user) and classroom.teacher != request.user:
        messages.error(request, 'Permission denied.')
        return redirect('classroom_list')

    if request.method == 'POST':
        enrollment = ClassroomEnrollment.objects.filter(classroom=classroom, student_id=student_id).first()
        if enrollment:
            student_name = enrollment.student.username
            enrollment.delete()
            messages.success(request, f'Student "{student_name}" removed from classroom.')
    return redirect('classroom_detail', pk=pk)


# ============================================
# Student Enrollment (Join Classroom)
# ============================================

@login_required
@user_passes_test(is_student)
def join_classroom(request):
    """View for a student to search and join a classroom."""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        password = request.POST.get('password', '').strip()

        if not code or not password:
            messages.error(request, 'You must enter the code and password.')
            return render(request, 'core/join_classroom.html')

        classroom = Classroom.objects.filter(code=code, is_active=True).first()
        if not classroom:
            messages.error(request, 'No classroom found with that code.')
            return render(request, 'core/join_classroom.html')

        if classroom.access_password != password:
            messages.error(request, 'Incorrect password.')
            return render(request, 'core/join_classroom.html')

        # Check if already enrolled
        if ClassroomEnrollment.objects.filter(classroom=classroom, student=request.user).exists():
            messages.warning(request, f'You are already enrolled in "{classroom.name}".')
            return render(request, 'core/join_classroom.html')

        ClassroomEnrollment.objects.create(classroom=classroom, student=request.user)
        messages.success(request, f'You have joined "{classroom.name}" with teacher {classroom.teacher.first_name or classroom.teacher.username}!')
        return redirect('dashboard')

    return render(request, 'core/join_classroom.html')


@login_required
@user_passes_test(is_student)
def my_classrooms(request):
    """View the classrooms the student is enrolled in."""
    enrollments = ClassroomEnrollment.objects.filter(student=request.user).select_related('classroom__teacher')
    return render(request, 'core/my_classrooms.html', {'enrollments': enrollments})


# ============================================
# Gemini AI Views
# ============================================
from .gemini_service import call_gemini, TUTOR_SYSTEM_PROMPT, GENERATE_QUESTIONS_PROMPT


@login_required
def ai_tutor_view(request):
    """Página del tutor IA para estudiantes."""
    conversations = AIConversation.objects.filter(user=request.user, purpose='tutor')[:20]
    return render(request, 'core/ai_tutor.html', {'conversations': conversations})


@login_required
@require_POST
def ai_tutor_chat(request):
    """Endpoint AJAX para enviar mensaje al tutor IA."""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Mensaje inválido.'}, status=400)

    if not user_message:
        return JsonResponse({'error': 'El mensaje no puede estar vacío.'}, status=400)

    if len(user_message) > 1000:
        return JsonResponse({'error': 'El mensaje es demasiado largo (máx. 1000 caracteres).'}, status=400)

    # Build context based on user role
    if request.user.is_staff:
        user_context = _build_teacher_context(request.user)
        context_label = "CONTEXTO_PROFESOR"
    else:
        user_context = _build_student_context(request.user)
        context_label = "CONTEXTO_ESTUDIANTE"

    # Build prompt with system context + user data
    full_prompt = (
        f"{TUTOR_SYSTEM_PROMPT}\n\n"
        f"[{context_label}]\n{user_context}\n[/{context_label}]\n\n"
        f"Usuario: {user_message}\n\nMateBot:"
    )

    result = call_gemini(full_prompt, temperature=0.7, max_tokens=1024)

    if not result['success']:
        return JsonResponse({'error': result['error']}, status=502)

    # Save to database
    conversation = AIConversation.objects.create(
        user=request.user,
        purpose='tutor',
        prompt=user_message,
        response=result['text'],
        tokens_used=result['tokens']
    )

    return JsonResponse({
        'response': result['text'],
        'tokens': result['tokens'],
        'id': conversation.id,
        'timestamp': conversation.created_at.strftime('%d/%m/%Y %H:%M')
    })


def _build_student_context(user):
    """Construye un resumen del progreso del estudiante para inyectar en el prompt."""
    from .models import UserLevelProgress, LevelAttempt, Discipline

    context_lines = []
    context_lines.append(f"Nombre: {user.first_name or user.username}")
    context_lines.append(f"Puntos totales: {user.total_points}")

    # Progress per discipline
    progress_list = UserLevelProgress.objects.filter(user=user).select_related('level__discipline')
    if progress_list.exists():
        # Group by discipline
        disciplines_data = {}
        for p in progress_list:
            disc_name = p.level.discipline.name
            if disc_name not in disciplines_data:
                disciplines_data[disc_name] = {'completed': 0, 'total_stars': 0, 'levels': []}
            disciplines_data[disc_name]['completed'] += 1
            disciplines_data[disc_name]['total_stars'] += p.stars
            disciplines_data[disc_name]['levels'].append(
                f"Nivel {p.level.number}: {p.stars} estrellas, puntaje {p.score}, {p.attempts} intentos"
            )

        context_lines.append(f"\nNiveles completados por disciplina:")
        for disc, info in disciplines_data.items():
            context_lines.append(f"- {disc}: {info['completed']} niveles, {info['total_stars']} estrellas")
            for lev in info['levels'][-5:]:  # Last 5 levels max
                context_lines.append(f"  • {lev}")
    else:
        context_lines.append("No ha completado ningún nivel todavía.")

    # Recent attempts (last 5)
    recent_attempts = LevelAttempt.objects.filter(user=user).select_related('level__discipline')[:5]
    if recent_attempts.exists():
        context_lines.append(f"\nÚltimos intentos:")
        for att in recent_attempts:
            context_lines.append(
                f"- {att.level.discipline.name} Nivel {att.level.number}: "
                f"puntaje {att.score}, {att.stars} estrellas, "
                f"tiempo {att.time_seconds}s ({att.created_at:%d/%m/%Y %H:%M})"
            )

    # Weak areas (levels with 1 star or many attempts)
    weak_levels = UserLevelProgress.objects.filter(
        user=user, stars__lte=1
    ).select_related('level__discipline')[:5]
    if weak_levels.exists():
        context_lines.append(f"\nÁreas donde necesita mejorar (1 estrella o menos):")
        for wl in weak_levels:
            context_lines.append(f"- {wl.level.discipline.name} Nivel {wl.level.number} ({wl.attempts} intentos, {wl.stars} estrellas)")

    return "\n".join(context_lines)


def _build_teacher_context(user):
    """Construye un resumen de datos de estudiantes para inyectar en el prompt del profesor."""
    from .models import UserLevelProgress, LevelAttempt, Discipline, Level, Classroom
    from django.contrib.auth import get_user_model
    from django.db.models import Avg, Count, Sum
    User = get_user_model()

    context_lines = []
    is_admin_user = user.is_superuser

    if is_admin_user:
        context_lines.append(f"Rol: Administrador (acceso global)")
        students = User.objects.filter(is_staff=False, is_superuser=False)
    else:
        context_lines.append(f"Rol: Profesor (acceso limitado a sus estudiantes)")
        students = get_teacher_students(user)
        # Show teacher's classrooms
        classrooms = Classroom.objects.filter(teacher=user)
        if classrooms.exists():
            context_lines.append(f"Grupos/Cursos del profesor:")
            for c in classrooms:
                context_lines.append(f"- {c.name} (código: {c.code}): {c.student_count} estudiantes")

    context_lines.append(f"Nombre: {user.first_name or user.username}")
    total_students = students.count()
    context_lines.append(f"\nTotal de estudiantes: {total_students}")

    # Disciplines overview
    disciplines = Discipline.objects.filter(is_active=True)
    context_lines.append(f"Disciplinas activas: {disciplines.count()}")
    for disc in disciplines:
        levels_count = disc.levels.filter(is_active=True).count()
        context_lines.append(f"- {disc.name}: {levels_count} niveles activos")

    # Student performance summary (top/bottom)
    student_stats = []
    for s in students[:30]:  # Limit to avoid huge prompts
        progress = UserLevelProgress.objects.filter(user=s)
        total_stars = progress.aggregate(Sum('stars'))['stars__sum'] or 0
        levels_done = progress.count()
        student_stats.append({
            'name': s.first_name or s.username,
            'points': s.total_points,
            'levels': levels_done,
            'stars': total_stars
        })

    if student_stats:
        # Sort by points desc
        student_stats.sort(key=lambda x: x['points'], reverse=True)

        context_lines.append(f"\nRanking de estudiantes (top 10):")
        for i, st in enumerate(student_stats[:10], 1):
            context_lines.append(
                f"  {i}. {st['name']}: {st['points']} pts, {st['levels']} niveles, {st['stars']} estrellas"
            )

        # Bottom performers
        struggling = [s for s in student_stats if s['levels'] == 0 or s['stars'] < 3]
        if struggling:
            context_lines.append(f"\nEstudiantes que necesitan atención ({len(struggling)}):")
            for st in struggling[:5]:
                context_lines.append(f"  - {st['name']}: {st['points']} pts, {st['levels']} niveles completados")

    # Recent activity (last 10 attempts - filtered by teacher's students)
    recent = LevelAttempt.objects.filter(user__in=students).select_related('user', 'level__discipline')[:10]
    if recent.exists():
        context_lines.append(f"\nActividad reciente (últimos intentos):")
        for att in recent:
            name = att.user.first_name or att.user.username
            context_lines.append(
                f"- {name} → {att.level.discipline.name} Nivel {att.level.number}: "
                f"{att.score} pts, {att.stars}★, {att.time_seconds}s ({att.created_at:%d/%m/%Y %H:%M})"
            )

    # General averages (filtered)
    avg_data = LevelAttempt.objects.filter(user__in=students).aggregate(
        avg_score=Avg('score'),
        avg_stars=Avg('stars'),
        avg_time=Avg('time_seconds'),
        total_attempts=Count('id')
    )
    if avg_data['total_attempts']:
        context_lines.append(f"\nEstadísticas generales:")
        context_lines.append(f"- Total de intentos: {avg_data['total_attempts']}")
        context_lines.append(f"- Puntaje promedio: {avg_data['avg_score']:.1f}")
        context_lines.append(f"- Estrellas promedio: {avg_data['avg_stars']:.1f}")
        context_lines.append(f"- Tiempo promedio: {avg_data['avg_time']:.0f}s")

    return "\n".join(context_lines)


@login_required
@user_passes_test(is_management_user)
@require_POST
def ai_generate_questions(request):
    """Endpoint AJAX para generar preguntas con IA (solo profesores)."""
    try:
        data = json.loads(request.body)
        topic = data.get('topic', '').strip()
        question_type = data.get('question_type', 'option')
        count = int(data.get('count', 3))
        difficulty = data.get('difficulty', 'fácil')
    except (json.JSONDecodeError, AttributeError, ValueError):
        return JsonResponse({'error': 'Datos inválidos.'}, status=400)

    if not topic:
        return JsonResponse({'error': 'Debes indicar un tema.'}, status=400)

    count = min(max(count, 1), 10)  # Between 1 and 10

    # Build specific prompt based on question type
    type_instructions = {
        'option': 'Cada objeto debe tener: "text" (pregunta), "options" (array de 4 opciones), "correct" (índice 0-3 de la opción correcta).',
        'writing': 'Cada objeto debe tener: "text" (pregunta), "correct_answer" (respuesta correcta como texto).',
        'voice': 'Cada objeto debe tener: "text" (pregunta), "correct_answer" (respuesta correcta como texto corto, preferiblemente un número o palabra).',
    }

    instruction = type_instructions.get(question_type, type_instructions['option'])

    full_prompt = (
        f"{GENERATE_QUESTIONS_PROMPT}\n\n"
        f"Genera {count} preguntas de matemáticas sobre: {topic}.\n"
        f"Dificultad: {difficulty}.\n"
        f"Tipo de pregunta: {question_type}.\n"
        f"{instruction}\n"
        f"Responde SOLO con el array JSON."
    )

    result = call_gemini(full_prompt, temperature=0.8, max_tokens=2048)

    if not result['success']:
        return JsonResponse({'error': result['error']}, status=502)

    # Try to parse JSON from response
    raw_text = result['text'].strip()
    if raw_text.startswith('```'):
        raw_text = raw_text.split('\n', 1)[1] if '\n' in raw_text else raw_text
        raw_text = raw_text.rsplit('```', 1)[0]

    try:
        questions = json.loads(raw_text)
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'La IA no generó un formato válido. Intenta de nuevo.',
            'raw': result['text']
        }, status=422)

    # Save to database
    AIConversation.objects.create(
        user=request.user,
        purpose='generate',
        prompt=f"Tema: {topic} | Tipo: {question_type} | Cantidad: {count} | Dificultad: {difficulty}",
        response=result['text'],
        tokens_used=result['tokens']
    )

    return JsonResponse({
        'questions': questions,
        'tokens': result['tokens']
    })
