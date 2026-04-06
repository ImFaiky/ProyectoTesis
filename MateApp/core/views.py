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
from datetime import timedelta
from django.utils import timezone
from .models import Discipline, Level, UserLevelProgress, LevelAttempt
from .services import save_level_progress
from .forms import DisciplineForm, LevelForm

from django.core.paginator import Paginator

User = get_user_model()


def is_admin(user):
    return user.is_superuser

def is_management_user(user):
    return user.is_staff  # Both superusers and staff can manage

def is_student(user):
    return not user.is_staff and user.is_authenticated

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

class DisciplineCreateView(LoginRequiredMixin, ManagementRequiredMixin, CreateView):
    model = Discipline
    form_class = DisciplineForm
    template_name = 'core/discipline_form.html'
    success_url = reverse_lazy('discipline_list')
    
    def form_valid(self, form):
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
    discipline = get_object_or_404(Discipline, id=discipline_id)
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
        kwargs['discipline'] = get_object_or_404(Discipline, id=self.kwargs.get('discipline_id'))
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
        context['discipline'] = get_object_or_404(Discipline, id=self.kwargs.get('discipline_id'))
        context['all_students'] = User.objects.filter(is_superuser=False, is_staff=False).order_by('username')
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['discipline'] = self.object.discipline
        context['all_students'] = User.objects.filter(is_superuser=False, is_staff=False).order_by('username')
        context['assigned_student_ids'] = list(self.object.assigned_students.values_list('id', flat=True))
        return context

@login_required
@user_passes_test(is_management_user)
def discipline_delete(request, discipline_id):
    discipline = get_object_or_404(Discipline, id=discipline_id)
    
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
    level = get_object_or_404(Level, id=level_id)
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
    if is_admin(request.user):
        # Admin Dashboard Logic
        student_count = User.objects.filter(is_superuser=False, is_staff=False).count()
        discipline_count = Discipline.objects.count()
        level_count = Level.objects.count()
        recent_progress = UserLevelProgress.objects.select_related('user', 'level').order_by('-completed_at')[:10]
        
        # Student Report Data
        students = User.objects.filter(is_superuser=False, is_staff=False).order_by('-total_points')
        
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
        
        # Discipline Performance Summary
        discipline_performance = []
        for discipline in Discipline.objects.all():
            total_progress = UserLevelProgress.objects.filter(level__discipline=discipline)
            discipline_performance.append({
                'discipline': discipline,
                'total_attempts': total_progress.count(),
                'unique_students': total_progress.values('user').distinct().count(),
                'avg_stars': total_progress.aggregate(models.Avg('stars'))['stars__avg'] or 0,
                'avg_score': total_progress.aggregate(models.Avg('score'))['score__avg'] or 0
            })
        
        # Overall Avg Score
        overall_avg_score = UserLevelProgress.objects.aggregate(models.Avg('score'))['score__avg'] or 0
        
        # Top Performers
        top_students = students[:5]
        
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
        })
    else:
        # Student Dashboard Logic
        disciplines = Discipline.objects.filter(is_active=True)
        return render(request, 'core/dashboard.html', {'disciplines': disciplines})

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
    students_qs = User.objects.filter(is_superuser=False, is_staff=False).order_by('username')
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
    discipline = get_object_or_404(Discipline, id=discipline_id)
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
    
    # Filter progress by date
    progress_qs = UserLevelProgress.objects.all()
    if date_from:
        progress_qs = progress_qs.filter(completed_at__gte=date_from)
    
    # Student data (top 10 by points earned in period)
    students = User.objects.filter(is_superuser=False, is_staff=False)
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
    
    # Discipline data
    discipline_data = []
    for discipline in Discipline.objects.all():
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
    """General analytics: attempts and time per level across all students."""
    disciplines = Discipline.objects.filter(is_active=True).prefetch_related('levels')
    
    # Build per-level stats from LevelAttempt
    level_stats = []
    for discipline in disciplines:
        for level in discipline.levels.filter(is_active=True).order_by('number'):
            attempts = LevelAttempt.objects.filter(level=level)
            attempt_count = attempts.count()
            if attempt_count == 0:
                continue
            avg_time = attempts.aggregate(models.Avg('time_seconds'))['time_seconds__avg'] or 0
            avg_score = attempts.aggregate(models.Avg('score'))['score__avg'] or 0
            min_time = attempts.aggregate(models.Min('time_seconds'))['time_seconds__min'] or 0
            max_time = attempts.aggregate(models.Max('time_seconds'))['time_seconds__max'] or 0
            unique_students = attempts.values('user').distinct().count()
            
            # Average attempts per student for this level
            progress_records = UserLevelProgress.objects.filter(level=level)
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
    
    # Per-student summary
    students = User.objects.filter(is_superuser=False, is_staff=False)
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
