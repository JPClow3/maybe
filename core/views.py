from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Count
from finance.models import Account, Transaction
from core.forms import CustomUserCreationForm

@require_http_methods(["GET", "POST"])
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    from datetime import date, timedelta
    from decimal import Decimal
    
    accounts = Account.objects.filter(user=request.user, status='active')
    transactions = Transaction.objects.filter(account__user=request.user)
    
    # Calculate "Caixa Livre" (Free Cash) - sum of depository account balances
    depository_accounts = accounts.filter(accountable_type='depository')
    free_cash = depository_accounts.aggregate(Sum('balance'))['balance__sum'] or Decimal('0')
    
    # Calculate "Fatura Atual" (Current Credit Card Bill) - sum of credit card balances (negative)
    credit_cards = accounts.filter(accountable_type='credit_card')
    credit_card_debt = credit_cards.aggregate(Sum('balance'))['balance__sum'] or Decimal('0')
    # Credit card balances are typically negative (debt), so we show absolute value
    current_bill = abs(credit_card_debt)
    
    # Calculate "Investimentos" (Investments) - sum of investment account balances
    investment_accounts = accounts.filter(accountable_type='investment')
    investments = investment_accounts.aggregate(Sum('balance'))['balance__sum'] or Decimal('0')
    
    # Calculate total balance (all active accounts)
    total_balance = accounts.aggregate(Sum('balance'))['balance__sum'] or Decimal('0')
    
    # Get recent transactions for display
    recent_transactions = transactions.order_by('-date', '-created_at')[:10]
    
    # Calculate spending comparison (this month vs last month) - simplified
    today = date.today()
    first_day_this_month = today.replace(day=1)
    if first_day_this_month.month == 1:
        first_day_last_month = first_day_this_month.replace(year=first_day_this_month.year - 1, month=12)
    else:
        first_day_last_month = first_day_this_month.replace(month=first_day_this_month.month - 1)
    
    this_month_expenses = transactions.filter(
        date__gte=first_day_this_month,
        excluded=False
    ).filter(category__classification='expense').aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    
    last_month_expenses = transactions.filter(
        date__gte=first_day_last_month,
        date__lt=first_day_this_month,
        excluded=False
    ).filter(category__classification='expense').aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    
    spending_change = Decimal('0')
    if last_month_expenses > 0:
        spending_change = ((this_month_expenses - last_month_expenses) / last_month_expenses) * 100
    
    context = {
        'free_cash': free_cash,
        'current_bill': current_bill,
        'investments': investments,
        'total_balance': total_balance,
        'spending_change': spending_change,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'core/dashboard.html', context)

@login_required
def dashboard_stats(request):
    """HTMX endpoint that returns only the dashboard stats cards"""
    from datetime import date, timedelta
    from decimal import Decimal
    
    accounts = Account.objects.filter(user=request.user, status='active')
    
    # Calculate "Caixa Livre" (Free Cash) - sum of depository account balances
    depository_accounts = accounts.filter(accountable_type='depository')
    free_cash = depository_accounts.aggregate(Sum('balance'))['balance__sum'] or Decimal('0')
    
    # Calculate "Fatura Atual" (Current Credit Card Bill) - sum of credit card balances (negative)
    credit_cards = accounts.filter(accountable_type='credit_card')
    credit_card_debt = credit_cards.aggregate(Sum('balance'))['balance__sum'] or Decimal('0')
    # Credit card balances are typically negative (debt), so we show absolute value
    current_bill = abs(credit_card_debt)
    
    # Calculate "Investimentos" (Investments) - sum of investment account balances
    investment_accounts = accounts.filter(accountable_type='investment')
    investments = investment_accounts.aggregate(Sum('balance'))['balance__sum'] or Decimal('0')
    
    context = {
        'free_cash': free_cash,
        'current_bill': current_bill,
        'investments': investments,
    }
    
    return render(request, 'core/dashboard_stats_partial.html', context)

def handler404(request, exception):
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    return render(request, 'errors/500.html', status=500)

def handler403(request, exception):
    return render(request, 'errors/403.html', status=403)

