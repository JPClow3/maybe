"""
Investment views for monitoring and asset allocation
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from decimal import Decimal
from datetime import date, timedelta
from investments.models import Security, SecurityPrice, Holding
from finance.models import Account


# Placeholder views - to be implemented
@login_required
def security_list(request):
    """
    List all securities.
    
    Note: Securities are global reference data (e.g., stock tickers like PETR4.SA),
    not user-specific. The Security model does not have a user relationship,
    so all users see the same security list. This is intentional design.
    """
    securities = Security.objects.all().order_by('ticker')
    context = {'securities': securities}
    return render(request, 'investments/security_list.html', context)


@login_required
def holding_list(request):
    """List all holdings"""
    holdings = Holding.objects.filter(account__user=request.user).order_by('-date')
    context = {'holdings': holdings}
    return render(request, 'investments/holding_list.html', context)


@login_required
def trade_list(request):
    """List all trades"""
    from investments.models import Trade
    trades = Trade.objects.filter(account__user=request.user).order_by('-date')
    context = {'trades': trades}
    return render(request, 'investments/trade_list.html', context)


@login_required
def b3_update_status(request):
    """View to check status of last B3 price update"""
    from investments.models import SecurityPrice
    
    # Get most recent price update
    latest_price = SecurityPrice.objects.filter(
        security__country_code='BR'
    ).order_by('-date').first()
    
    # Count securities with prices updated today
    today = date.today()
    securities_updated_today = SecurityPrice.objects.filter(
        security__country_code='BR',
        date=today
    ).values('security').distinct().count()
    
    total_br_securities = Security.objects.filter(country_code='BR').count()
    
    context = {
        'latest_price': latest_price,
        'securities_updated_today': securities_updated_today,
        'total_br_securities': total_br_securities,
        'update_percentage': (securities_updated_today / total_br_securities * 100) if total_br_securities > 0 else 0,
    }
    return render(request, 'investments/b3_update_status.html', context)


@login_required
def asset_allocation(request):
    """View showing asset allocation (pie chart data)"""
    # Get user's investment accounts
    investment_accounts = Account.objects.filter(
        user=request.user,
        accountable_type='investment',
        status='active'
    )
    
    # Calculate allocation by asset type
    # This is a simplified version - in production you'd want more sophisticated categorization
    allocation_data = []
    
    for account in investment_accounts:
        # Get account balance (includes holdings value)
        if account.balance:
            allocation_data.append({
                'name': account.name,
                'value': float(account.balance),
            })
    
    # Group by asset class if we have more data
    # For now, just show by account
    total_value = sum(item['value'] for item in allocation_data)
    
    context = {
        'allocation_data': allocation_data,
        'total_value': total_value,
    }
    return render(request, 'investments/asset_allocation.html', context)
