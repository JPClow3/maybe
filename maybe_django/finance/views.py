from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.db import IntegrityError, DatabaseError
from .models import Account, Transaction, Category

@login_required
def account_list(request):
    accounts = Account.objects.filter(user=request.user, status='active').order_by('name')
    return render(request, 'finance/account_list.html', {'accounts': accounts})

@login_required
def account_detail(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    transactions = Transaction.objects.filter(account=account).order_by('-date', '-created_at')[:20]
    context = {
        'account': account,
        'transactions': transactions,
    }
    return render(request, 'finance/account_detail.html', context)

@login_required
def account_new(request):
    from .forms import AccountForm
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            try:
                account = form.save(commit=False)
                account.user = request.user
                account.save()
                messages.success(request, f'Account "{account.name}" created successfully.')
                if is_htmx:
                    from django.http import HttpResponse
                    response = HttpResponse()
                    response['HX-Redirect'] = f'/accounts/{account.pk}/'
                    return response
                return redirect('account_detail', pk=account.pk)
            except IntegrityError:
                messages.error(request, 'An account with this name already exists. Please choose a different name.')
            except DatabaseError as e:
                messages.error(request, 'An error occurred while saving the account. Please try again.')
    else:
        form = AccountForm()
    
    if is_htmx and request.method == 'POST':
        return render(request, 'finance/account_form_partial.html', {'form': form})
    return render(request, 'finance/account_form.html', {'form': form, 'title': 'New Account'})

@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(account__user=request.user).order_by('-date', '-created_at')
    context = {
        'transactions': transactions,
    }
    return render(request, 'finance/transaction_list.html', context)

@login_required
def transaction_detail(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, account__user=request.user)
    return render(request, 'finance/transaction_detail.html', {'transaction': transaction})

@login_required
def transaction_new(request):
    from .forms import TransactionForm
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                transaction = form.save(commit=False)
                transaction.save()
                messages.success(request, f'Transaction "{transaction.name}" created successfully.')
                if is_htmx:
                    from django.http import HttpResponse
                    response = HttpResponse()
                    response['HX-Redirect'] = transaction.get_absolute_url() if hasattr(transaction, 'get_absolute_url') else f'/transactions/{transaction.pk}/'
                    return response
                return redirect('transaction_detail', pk=transaction.pk)
            except IntegrityError:
                messages.error(request, 'An error occurred while saving the transaction. Please check your input and try again.')
            except DatabaseError as e:
                messages.error(request, 'An error occurred while saving the transaction. Please try again.')
    else:
        form = TransactionForm(user=request.user)
    
    if is_htmx and request.method == 'POST':
        return render(request, 'finance/transaction_form_partial.html', {'form': form})
    return render(request, 'finance/transaction_form.html', {'form': form, 'title': 'New Transaction'})

@login_required
def account_edit(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    from .forms import AccountForm
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            try:
                account = form.save()
                messages.success(request, f'Account "{account.name}" updated successfully.')
                if is_htmx:
                    from django.http import HttpResponse
                    response = HttpResponse()
                    response['HX-Redirect'] = account.get_absolute_url() if hasattr(account, 'get_absolute_url') else f'/accounts/{account.pk}/'
                    return response
                return redirect('account_detail', pk=account.pk)
            except IntegrityError:
                messages.error(request, 'An error occurred while saving the account. Please check your input and try again.')
            except DatabaseError as e:
                messages.error(request, 'An error occurred while saving the account. Please try again.')
    else:
        form = AccountForm(instance=account)
    
    if is_htmx and request.method == 'POST':
        return render(request, 'finance/account_form_partial.html', {'form': form})
    return render(request, 'finance/account_form.html', {'form': form, 'title': 'Edit Account', 'account': account})

@login_required
def account_edit_inline(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    if not is_htmx:
        return redirect('account_detail', pk=account.pk)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            try:
                account.name = name
                account.save()
                messages.success(request, f'Account name updated to "{account.name}".')
                # Return the display version
                return render(request, 'finance/account_name_display.html', {'account': account})
            except (IntegrityError, DatabaseError):
                messages.error(request, 'An error occurred while saving. Please try again.')
        # On error, return edit form
        return render(request, 'finance/account_name_edit_inline.html', {'account': account})
    else:
        # GET request - return edit form
        return render(request, 'finance/account_name_edit_inline.html', {'account': account})

@login_required
def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, account__user=request.user)
    from .forms import TransactionForm
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            try:
                transaction = form.save()
                messages.success(request, f'Transaction "{transaction.name}" updated successfully.')
                if is_htmx:
                    from django.http import HttpResponse
                    response = HttpResponse()
                    response['HX-Redirect'] = transaction.get_absolute_url() if hasattr(transaction, 'get_absolute_url') else f'/transactions/{transaction.pk}/'
                    return response
                return redirect('transaction_detail', pk=transaction.pk)
            except IntegrityError:
                messages.error(request, 'An error occurred while saving the transaction. Please check your input and try again.')
            except DatabaseError as e:
                messages.error(request, 'An error occurred while saving the transaction. Please try again.')
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    
    if is_htmx and request.method == 'POST':
        return render(request, 'finance/transaction_form_partial.html', {'form': form})
    return render(request, 'finance/transaction_form.html', {'form': form, 'title': 'Edit Transaction', 'transaction': transaction})

