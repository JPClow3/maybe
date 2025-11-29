from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Security, Holding, Trade

@login_required
def security_list(request):
    search_query = request.GET.get('search', '')
    securities = Security.objects.all()
    
    if search_query:
        securities = securities.filter(
            Q(ticker__icontains=search_query) |
            Q(name__icontains=search_query)
        )
    
    securities = securities.order_by('ticker')
    return render(request, 'investments/security_list.html', {
        'securities': securities,
        'search_query': search_query,
    })

@login_required
def holding_list(request):
    account_id = request.GET.get('account', '')
    holdings = Holding.objects.filter(account__user=request.user).select_related('account', 'security')
    
    if account_id:
        holdings = holdings.filter(account_id=account_id)
    
    holdings = holdings.order_by('-date', 'account__name', 'security__ticker')
    return render(request, 'investments/holding_list.html', {
        'holdings': holdings,
        'account_id': account_id,
    })

@login_required
def trade_list(request):
    account_id = request.GET.get('account', '')
    security_id = request.GET.get('security', '')
    trades = Trade.objects.filter(account__user=request.user).select_related('account', 'security')
    
    if account_id:
        trades = trades.filter(account_id=account_id)
    if security_id:
        trades = trades.filter(security_id=security_id)
    
    trades = trades.order_by('-date', 'account__name', 'security__ticker')
    return render(request, 'investments/trade_list.html', {
        'trades': trades,
        'account_id': account_id,
        'security_id': security_id,
    })

