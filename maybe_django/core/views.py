from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Count
from finance.models import Account, Transaction

@require_http_methods(["GET", "POST"])
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    accounts = Account.objects.filter(user=request.user, status='active')
    transactions = Transaction.objects.filter(account__user=request.user)
    
    context = {
        'accounts_count': accounts.count(),
        'total_balance': accounts.aggregate(Sum('balance'))['balance__sum'] or 0,
        'recent_accounts': accounts.order_by('-updated_at')[:5],
        'recent_transactions': transactions.order_by('-date', '-created_at')[:10],
        'recent_transactions_count': transactions.count(),
    }
    
    return render(request, 'core/dashboard.html', context)

def handler404(request, exception):
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    return render(request, 'errors/500.html', status=500)

def handler403(request, exception):
    return render(request, 'errors/403.html', status=403)

