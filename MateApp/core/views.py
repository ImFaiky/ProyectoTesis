from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Discipline, Level, UserLevelProgress
from .services import save_level_progress
from .forms import DisciplineForm, LevelForm
import json

User = get_user_model()


def is_admin(user):
    return user.is_superuser or user.is_staff

def is_student(user):
    return not user.is_superuser and not user.is_staff

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_admin(self.request.user)

# --- Discipline Views ---
class DisciplineListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Discipline
    template_name = 'core/discipline_list.html'
    context_object_name = 'disciplines'

class DisciplineCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Discipline
    form_class = DisciplineForm
    template_name = 'core/discipline_form.html'
    success_url = reverse_lazy('discipline_list')

class DisciplineUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Discipline
    form_class = DisciplineForm
    template_name = 'core/discipline_form.html'
    success_url = reverse_lazy('discipline_list')

# --- Level Views ---
@login_required
@user_passes_test(is_admin)
def level_list(request, discipline_id):
    discipline = get_object_or_404(Discipline, id=discipline_id)
    levels = discipline.levels.all().order_by('number')
    return render(request, 'core/level_list.html', {'discipline': discipline, 'levels': levels})

class LevelCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Level
    form_class = LevelForm
    template_name = 'core/level_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['discipline'] = get_object_or_404(Discipline, id=self.kwargs.get('discipline_id'))
        return kwargs

    def form_valid(self, form):
        form.instance.discipline_id = self.kwargs.get('discipline_id')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('level_list', kwargs={'discipline_id': self.kwargs['discipline_id']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['discipline'] = get_object_or_404(Discipline, id=self.kwargs.get('discipline_id'))
        return context

class LevelUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Level
    form_class = LevelForm
    template_name = 'core/level_form.html'

    def get_success_url(self):
        return reverse_lazy('level_list', kwargs={'discipline_id': self.object.discipline.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['discipline'] = self.object.discipline
        return context


# --- Existing Views ---

@login_required
def dashboard(request):
    if is_admin(request.user):
        # Admin Dashboard Logic
        student_count = User.objects.filter(is_superuser=False, is_staff=False).count()
        discipline_count = Discipline.objects.count()
        level_count = Level.objects.count()
        recent_progress = UserLevelProgress.objects.select_related('user', 'level').order_by('-completed_at')[:10]
        
        return render(request, 'core/admin_dashboard.html', {
            'student_count': student_count,
            'discipline_count': discipline_count,
            'level_count': level_count,
            'recent_progress': recent_progress,
        })
    else:
        # Student Dashboard Logic
        disciplines = Discipline.objects.filter(is_active=True)
        return render(request, 'core/dashboard.html', {'disciplines': disciplines})

@login_required
def discipline_detail(request, discipline_id):
    # Only students should play, but admins might want to see? 
    # For now, let's allow both but generally this view is for playing.
    discipline = get_object_or_404(Discipline, id=discipline_id)
    levels = discipline.levels.filter(is_active=True).order_by('number')
    
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
        
        save_level_progress(request.user, level, score, stars)
        
        return redirect('discipline_detail', discipline_id=level.discipline.id)
    
    return render(request, 'core/play_level.html', {'level': level})

@login_required
@user_passes_test(is_admin)
def student_list(request):
    students = User.objects.filter(is_superuser=False, is_staff=False)
    return render(request, 'core/student_list.html', {'students': students})

@login_required
@user_passes_test(is_admin)
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
