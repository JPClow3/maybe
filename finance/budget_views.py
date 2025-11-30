"""
Budget views for managing monthly budgets
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import HttpResponse
from decimal import Decimal
from datetime import date, timedelta
from .models import Budget, BudgetCategory, Category, Transaction
from .utils import add_toast_trigger


@login_required
def budget_list(request):
    """List all budgets for the user"""
    budgets = Budget.objects.filter(user=request.user).order_by('-start_date')
    context = {
        'budgets': budgets,
    }
    return render(request, 'finance/budget_list.html', context)


@login_required
def budget_detail(request, pk):
    """View budget details with category breakdown"""
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    
    # Get budget categories with actual spending
    budget_categories = budget.budget_categories.all().select_related('category')
    for bc in budget_categories:
        bc.actual = budget.budget_category_actual_spending(bc)
        bc.available = (bc.budgeted_spending or Decimal('0')) - bc.actual
    
    context = {
        'budget': budget,
        'budget_categories': budget_categories,
    }
    return render(request, 'finance/budget_detail.html', context)


@login_required
def budget_create(request):
    """Create a new budget"""
    from datetime import datetime
    
    if request.method == 'POST':
        # Get month/year from form
        month_str = request.POST.get('month', '')
        budgeted_spending = request.POST.get('budgeted_spending', '')
        
        try:
            # Parse month (format: YYYY-MM)
            year, month = map(int, month_str.split('-'))
            start_date = date(year, month, 1)
            
            # Calculate end_date (last day of month)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            # Create budget
            budget = Budget.objects.create(
                user=request.user,
                start_date=start_date,
                end_date=end_date,
                budgeted_spending=Decimal(budgeted_spending.replace(',', '.')) if budgeted_spending else None,
                currency=request.user.currency
            )
            
            # Sync budget categories
            budget.sync_budget_categories()
            
            messages.success(request, f'Orçamento de {start_date.strftime("%B %Y")} criado com sucesso!')
            return redirect('budget_detail', pk=budget.pk)
        except (ValueError, TypeError) as e:
            messages.error(request, f'Erro ao criar orçamento: {str(e)}')
    
    # GET request - show form
    today = date.today()
    current_month = today.strftime('%Y-%m')
    context = {
        'current_month': current_month,
    }
    return render(request, 'finance/budget_form.html', context)


@login_required
def budget_edit(request, pk):
    """Edit an existing budget"""
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    
    if request.method == 'POST':
        budgeted_spending = request.POST.get('budgeted_spending', '')
        expected_income = request.POST.get('expected_income', '')
        
        try:
            if budgeted_spending:
                budget.budgeted_spending = Decimal(budgeted_spending.replace(',', '.'))
            else:
                budget.budgeted_spending = None
            
            if expected_income:
                budget.expected_income = Decimal(expected_income.replace(',', '.'))
            else:
                budget.expected_income = None
            
            budget.save()
            messages.success(request, 'Orçamento atualizado com sucesso!')
            return redirect('budget_detail', pk=budget.pk)
        except (ValueError, TypeError) as e:
            messages.error(request, f'Erro ao atualizar orçamento: {str(e)}')
    
    # GET request - show form
    context = {
        'budget': budget,
    }
    return render(request, 'finance/budget_form.html', context)


@login_required
def budget_category_update(request, budget_pk, category_pk):
    """Update budget category spending limit"""
    budget = get_object_or_404(Budget, pk=budget_pk, user=request.user)
    budget_category = get_object_or_404(BudgetCategory, pk=category_pk, budget=budget)
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    if request.method == 'POST':
        budgeted_spending = request.POST.get('budgeted_spending', '')
        
        try:
            if budgeted_spending:
                budget_category.budgeted_spending = Decimal(budgeted_spending.replace(',', '.'))
            else:
                budget_category.budgeted_spending = None
            budget_category.save()
            
            if is_htmx:
                response = HttpResponse(status=204)
                response['HX-Trigger'] = 'budgetUpdated'
                add_toast_trigger(response, 'Categoria atualizada!', 'success')
                return response
            messages.success(request, 'Categoria atualizada!')
        except (ValueError, TypeError) as e:
            if is_htmx:
                response = HttpResponse(status=400)
                add_toast_trigger(response, f'Erro: {str(e)}', 'error')
                return response
            messages.error(request, f'Erro: {str(e)}')
    
    return redirect('budget_detail', pk=budget.pk)


@login_required
def budget_available_to_spend(request, category_id=None):
    """Calculate how much can be spent in a category (for weekend/week calculation)"""
    from datetime import datetime, timedelta
    
    today = date.today()
    current_month_start = today.replace(day=1)
    
    # Get current month budget
    try:
        budget = Budget.objects.get(
            user=request.user,
            start_date=current_month_start
        )
    except Budget.DoesNotExist:
        return HttpResponse('Nenhum orçamento encontrado para este mês', status=404)
    
    if category_id:
        # Category-specific calculation
        try:
            category = Category.objects.get(pk=category_id, user=request.user)
            budget_category = budget.budget_categories.filter(category=category).first()
            
            if not budget_category:
                return HttpResponse('Categoria não encontrada no orçamento', status=404)
            
            actual = budget.budget_category_actual_spending(budget_category)
            budgeted = budget_category.budgeted_spending or Decimal('0')
            available = budgeted - actual
            
            # Calculate available until end of week
            days_remaining = (today - current_month_start).days + 1
            days_in_month = (budget.end_date - current_month_start).days + 1
            daily_rate = available / max(days_in_month - days_remaining + 1, 1)
            
            # Days until end of week (Sunday)
            days_until_weekend = (6 - today.weekday()) + 1  # +1 to include today
            available_until_weekend = daily_rate * days_until_weekend
            
            context = {
                'category': category,
                'budgeted': budgeted,
                'actual': actual,
                'available': available,
                'available_until_weekend': available_until_weekend,
                'days_until_weekend': days_until_weekend,
            }
            return render(request, 'finance/budget_available_to_spend.html', context)
        except Category.DoesNotExist:
            return HttpResponse('Categoria não encontrada', status=404)
    else:
        # Overall budget calculation
        available = budget.available_to_spend
        context = {
            'budget': budget,
            'available': available,
        }
        return render(request, 'finance/budget_available_overall.html', context)

