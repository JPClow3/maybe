import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.db import IntegrityError, DatabaseError
from django.http import HttpResponse
from decimal import Decimal, InvalidOperation
from .models import Account, Transaction, Category
from .utils import add_toast_trigger, parse_brazilian_currency

logger = logging.getLogger(__name__)

@login_required
def account_list(request):
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    # If HTMX request with skeleton parameter, return skeleton
    if is_htmx and request.GET.get('skeleton'):
        return render(request, 'finance/account_list_skeleton.html')
    
    # For initial page load, show skeleton and load content via HTMX
    accounts = Account.objects.filter(user=request.user, status='active').order_by('name')
    
    # Calculate summary statistics
    asset_accounts = accounts.filter(
        accountable_type__in=['depository', 'investment', 'crypto', 'property', 'vehicle', 'other_asset']
    )
    liability_accounts = accounts.filter(
        accountable_type__in=['credit_card', 'loan', 'other_liability']
    )
    
    total_assets = asset_accounts.aggregate(Sum('balance'))['balance__sum'] or Decimal('0')
    total_liabilities = abs(liability_accounts.aggregate(Sum('balance'))['balance__sum'] or Decimal('0'))
    net_worth = total_assets - total_liabilities
    
    context = {
        'accounts': accounts,
        'show_skeleton': not is_htmx,  # Show skeleton on initial load, not on HTMX requests
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'net_worth': net_worth,
        'account_count': accounts.count(),
    }
    return render(request, 'finance/account_list.html', context)

@login_required
def account_list_data(request):
    """HTMX endpoint that returns only the account list content"""
    accounts = Account.objects.filter(user=request.user, status='active').order_by('name')
    
    # Calculate summary statistics
    asset_accounts = accounts.filter(
        accountable_type__in=['depository', 'investment', 'crypto', 'property', 'vehicle', 'other_asset']
    )
    liability_accounts = accounts.filter(
        accountable_type__in=['credit_card', 'loan', 'other_liability']
    )
    
    total_assets = asset_accounts.aggregate(Sum('balance'))['balance__sum'] or Decimal('0')
    total_liabilities = abs(liability_accounts.aggregate(Sum('balance'))['balance__sum'] or Decimal('0'))
    net_worth = total_assets - total_liabilities
    
    return render(request, 'finance/account_list_data.html', {
        'accounts': accounts,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'net_worth': net_worth,
        'account_count': accounts.count(),
    })

@login_required
def account_detail(request, pk):
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    # If HTMX request with skeleton parameter, return skeleton
    if is_htmx and request.GET.get('skeleton'):
        return render(request, 'finance/account_detail_skeleton.html')
    
    account = get_object_or_404(Account, pk=pk, user=request.user)
    transactions = Transaction.objects.filter(account=account).order_by('-date', '-created_at')[:20]
    context = {
        'account': account,
        'transactions': transactions,
        'show_skeleton': not is_htmx,  # Show skeleton on initial load, not on HTMX requests
    }
    return render(request, 'finance/account_detail.html', context)

@login_required
def account_detail_data(request, pk):
    """HTMX endpoint that returns only the account detail content"""
    account = get_object_or_404(Account, pk=pk, user=request.user)
    transactions = Transaction.objects.filter(account=account).order_by('-date', '-created_at')[:20]
    context = {
        'account': account,
        'transactions': transactions,
    }
    return render(request, 'finance/account_detail_data.html', context)

@login_required
def account_validate_field(request):
    """HTMX endpoint for real-time field validation"""
    from .forms import AccountForm
    field_name = request.GET.get('field')
    field_value = request.GET.get('value', '')
    
    if not field_name:
        return HttpResponse('', status=400)
    
    # Create a minimal form instance to validate the field
    # For uniqueness validation, we need user context
    form_data = {field_name: field_value}
    form = AccountForm(form_data, user=request.user)
    
    # Validate only the specific field
    if field_name in form.fields:
        try:
            form.full_clean()
            field = form[field_name]
            
            if field.errors:
                return render(request, 'partials/field_error.html', {
                    'errors': field.errors,
                    'field_id': field.id_for_label
                })
            else:
                return render(request, 'partials/field_success.html', {
                    'field_id': field.id_for_label
                })
        except Exception as e:
            # Log validation errors for debugging
            logger.exception("Error validating account field '%s' with value '%s': %s", field_name, field_value, e)
            # Return empty response to avoid exposing internal errors
            return HttpResponse('', status=400)
    
    return HttpResponse('', status=400)

@login_required
def account_new(request):
    from .forms import AccountForm
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    if request.method == 'POST':
        form = AccountForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                account = form.save(commit=False)
                account.user = request.user
                account.save()
                if is_htmx:
                    response = HttpResponse(status=204)
                    response['HX-Trigger'] = 'accountListChanged'
                    add_toast_trigger(response, f'Conta "{account.name}" criada com sucesso!', 'success')
                    return response
                messages.success(request, f'Conta "{account.name}" criada com sucesso!')
                return redirect('account_detail', pk=account.pk)
            except IntegrityError:
                form.add_error('name', 'Já existe uma conta com este nome. Por favor, escolha outro nome.')
                if is_htmx:
                    return render(request, 'finance/account_form_partial.html', {'form': form})
                messages.error(request, 'Já existe uma conta com este nome. Por favor, escolha outro nome.')
            except DatabaseError as e:
                logger.error("Database error saving account: %s", e, exc_info=True)
                form.add_error(None, 'Ocorreu um erro ao salvar a conta. Por favor, tente novamente.')
                if is_htmx:
                    return render(request, 'finance/account_form_partial.html', {'form': form})
                messages.error(request, 'Ocorreu um erro ao salvar a conta. Por favor, tente novamente.')
        else:
            # Form validation failed - return form with errors
            if is_htmx:
                return render(request, 'finance/account_form_partial.html', {'form': form})
    else:
        form = AccountForm(user=request.user)
    
    if is_htmx:
        return render(request, 'finance/account_form_partial.html', {'form': form})
    return render(request, 'finance/account_form.html', {'form': form, 'title': 'New Account'})

@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(account__user=request.user).order_by('-date', '-created_at')
    categories = Category.objects.filter(user=request.user)
    context = {
        'transactions': transactions,
        'categories': categories,
    }
    return render(request, 'finance/transaction_list.html', context)

@login_required
def transaction_list_data(request):
    """HTMX endpoint that returns only the transaction list table"""
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    transactions = Transaction.objects.filter(account__user=request.user).order_by('-date', '-created_at')
    categories = Category.objects.filter(user=request.user)
    
    # Pagination
    paginator = Paginator(transactions, 50)  # 50 items per page
    page = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'transactions': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'categories': categories,
    }
    return render(request, 'finance/transaction_list_table_partial.html', context)

@login_required
def transaction_quick_form(request):
    """HTMX endpoint that returns quick transaction form for mobile"""
    from .models import Account
    
    # Get recent transaction names for autocomplete (last 20 unique names)
    recent_names = Transaction.objects.filter(
        account__user=request.user
    ).values_list('name', flat=True).distinct()[:20]
    
    # Get categories
    categories = Category.objects.filter(user=request.user).order_by('name')
    
    # Get default account (first active account)
    default_account = Account.objects.filter(user=request.user, status='active').first()
    
    context = {
        'recent_names': recent_names,
        'categories': categories,
        'default_account': default_account,
    }
    return render(request, 'finance/transaction_quick_form_partial.html', context)

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
                if is_htmx:
                    response = HttpResponse(status=204)
                    response['HX-Trigger'] = 'transactionListChanged'
                    add_toast_trigger(response, f'Transação "{transaction.name}" criada com sucesso!', 'success')
                    return response
                messages.success(request, f'Transação "{transaction.name}" criada com sucesso!')
                return redirect('transaction_detail', pk=transaction.pk)
            except IntegrityError:
                form.add_error(None, 'Ocorreu um erro ao salvar a transação. Verifique os dados e tente novamente.')
                if is_htmx:
                    return render(request, 'finance/transaction_form_partial.html', {'form': form})
                messages.error(request, 'Ocorreu um erro ao salvar a transação. Verifique os dados e tente novamente.')
            except DatabaseError as e:
                logger.error("Database error saving transaction: %s", e, exc_info=True)
                form.add_error(None, 'Ocorreu um erro ao salvar a transação. Por favor, tente novamente.')
                if is_htmx:
                    return render(request, 'finance/transaction_form_partial.html', {'form': form})
                messages.error(request, 'Ocorreu um erro ao salvar a transação. Por favor, tente novamente.')
        else:
            # Form validation failed - return form with errors
            if is_htmx:
                return render(request, 'finance/transaction_form_partial.html', {'form': form})
            # Non-HTMX: fall through to render form with errors at the end
    else:
        form = TransactionForm(user=request.user)
    
    if is_htmx:
        return render(request, 'finance/transaction_form_partial.html', {'form': form})
    return render(request, 'finance/transaction_form.html', {'form': form, 'title': 'New Transaction'})

@login_required
def account_edit(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    from .forms import AccountForm
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account, user=request.user)
        if form.is_valid():
            try:
                account = form.save()
                if is_htmx:
                    response = HttpResponse(status=204)
                    response['HX-Trigger'] = 'accountListChanged'
                    add_toast_trigger(response, f'Conta "{account.name}" atualizada com sucesso!', 'success')
                    return response
                messages.success(request, f'Conta "{account.name}" atualizada com sucesso!')
                return redirect('account_detail', pk=account.pk)
            except IntegrityError:
                form.add_error('name', 'Já existe uma conta com este nome. Por favor, escolha outro nome.')
                if is_htmx:
                    return render(request, 'finance/account_form_partial.html', {'form': form})
                messages.error(request, 'Ocorreu um erro ao salvar a conta. Verifique os dados e tente novamente.')
            except DatabaseError as e:
                logger.error("Database error saving account: %s", e, exc_info=True)
                form.add_error(None, 'Ocorreu um erro ao salvar a conta. Por favor, tente novamente.')
                if is_htmx:
                    return render(request, 'finance/account_form_partial.html', {'form': form})
                messages.error(request, 'Ocorreu um erro ao salvar a conta. Por favor, tente novamente.')
        else:
            # Form validation failed - return form with errors
            if is_htmx:
                return render(request, 'finance/account_form_partial.html', {'form': form})
    else:
        form = AccountForm(instance=account, user=request.user)
    
    if is_htmx:
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
                messages.success(request, f'Nome da conta atualizado para "{account.name}".')
                # Return the display version
                return render(request, 'finance/account_name_display.html', {'account': account})
            except (IntegrityError, DatabaseError):
                messages.error(request, 'Ocorreu um erro ao salvar. Por favor, tente novamente.')
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
                if is_htmx:
                    response = HttpResponse(status=204)
                    response['HX-Trigger'] = 'transactionListChanged'
                    add_toast_trigger(response, f'Transação "{transaction.name}" atualizada com sucesso!', 'success')
                    return response
                messages.success(request, f'Transação "{transaction.name}" atualizada com sucesso!')
                return redirect('transaction_detail', pk=transaction.pk)
            except IntegrityError:
                form.add_error(None, 'Ocorreu um erro ao salvar a transação. Verifique os dados e tente novamente.')
                if is_htmx:
                    return render(request, 'finance/transaction_form_partial.html', {'form': form})
                messages.error(request, 'Ocorreu um erro ao salvar a transação. Verifique os dados e tente novamente.')
            except DatabaseError as e:
                logger.error("Database error saving transaction: %s", e, exc_info=True)
                form.add_error(None, 'Ocorreu um erro ao salvar a transação. Por favor, tente novamente.')
                if is_htmx:
                    return render(request, 'finance/transaction_form_partial.html', {'form': form})
                messages.error(request, 'Ocorreu um erro ao salvar a transação. Por favor, tente novamente.')
        else:
            # Form validation failed - return form with errors
            if is_htmx:
                return render(request, 'finance/transaction_form_partial.html', {'form': form})
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    
    if is_htmx:
        return render(request, 'finance/transaction_form_partial.html', {'form': form})
    return render(request, 'finance/transaction_form.html', {'form': form, 'title': 'Edit Transaction', 'transaction': transaction})

@login_required
def transaction_update_category(request, pk):
    """Update transaction category inline via HTMX"""
    transaction = get_object_or_404(Transaction, pk=pk, account__user=request.user)
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    if not is_htmx:
        return redirect('transaction_detail', pk=transaction.pk)
    
    if request.method == 'POST':
        category_id = request.POST.get('category_id', '').strip()
        try:
            if category_id:
                category = Category.objects.get(pk=category_id, user=request.user)
                transaction.category = category
            else:
                transaction.category = None
            transaction.save()
            
            # Return updated display cell
            response = render(request, 'finance/transaction_category_cell.html', {
                'transaction': transaction,
                'categories': Category.objects.filter(user=request.user)
            })
            add_toast_trigger(response, 'Categoria atualizada!', 'success')
            return response
        except (Category.DoesNotExist, ValueError):
            error_response = render(request, 'finance/transaction_category_cell.html', {
                'transaction': transaction,
                'categories': Category.objects.filter(user=request.user)
            })
            add_toast_trigger(error_response, 'Erro ao atualizar categoria.', 'error')
            return error_response
    
    # GET request - return edit form
    return render(request, 'finance/transaction_category_edit.html', {
        'transaction': transaction,
        'categories': Category.objects.filter(user=request.user)
    })

@login_required
def transaction_delete(request, pk):
    """Delete a transaction"""
    transaction = get_object_or_404(Transaction, pk=pk, account__user=request.user)
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    if request.method == 'POST':
        transaction_name = transaction.name
        transaction.delete()
        
        if is_htmx:
            # Return empty response to remove the row
            return HttpResponse('')
        messages.success(request, f'Transação "{transaction_name}" excluída com sucesso!')
        return redirect('transaction_list')
    
    # GET request - show confirmation (for non-HTMX)
    return render(request, 'finance/transaction_confirm_delete.html', {'transaction': transaction})

@login_required
def transaction_duplicate(request, pk):
    """Duplicate a transaction"""
    original = get_object_or_404(Transaction, pk=pk, account__user=request.user)
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    if request.method == 'POST':
        # Create a copy of the transaction
        duplicate = Transaction.objects.create(
            account=original.account,
            date=original.date,
            amount=original.amount,
            currency=original.currency,
            name=f"{original.name} (cópia)",
            notes=original.notes,
            category=original.category,
            merchant=original.merchant,
            kind=original.kind,
        )
        
        if is_htmx:
            response = HttpResponse(status=204)
            response['HX-Trigger'] = 'transactionListChanged'
            add_toast_trigger(response, f'Transação duplicada com sucesso!', 'success')
            return response
        messages.success(request, 'Transação duplicada com sucesso!')
        return redirect('transaction_detail', pk=duplicate.pk)
    
    # GET request - redirect to edit with pre-filled form
    from .forms import TransactionForm
    form = TransactionForm(instance=original, user=request.user)
    form.initial['name'] = f"{original.name} (cópia)"
    return render(request, 'finance/transaction_form.html', {'form': form, 'title': 'Duplicar Transação'})

@login_required
def transaction_update_amount(request, pk):
    """Update transaction amount inline via HTMX"""
    transaction = get_object_or_404(Transaction, pk=pk, account__user=request.user)
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    if not is_htmx:
        return redirect('transaction_detail', pk=transaction.pk)
    
    if request.method == 'POST':
        amount_str = request.POST.get('amount', '').strip()
        try:
            # Convert Brazilian format to decimal using shared utility
            amount = parse_brazilian_currency(amount_str)
            transaction.amount = amount
            transaction.save()
            
            # Return updated display cell
            response = render(request, 'finance/transaction_amount_cell.html', {'transaction': transaction})
            add_toast_trigger(response, 'Valor atualizado!', 'success')
            return response
        except (ValueError, TypeError, InvalidOperation):
            error_response = render(request, 'finance/transaction_amount_cell.html', {'transaction': transaction})
            add_toast_trigger(error_response, 'Erro ao atualizar valor. Use formato: R$ 1.234,56', 'error')
            return error_response
    
    # GET request - return edit form
    return render(request, 'finance/transaction_amount_edit.html', {'transaction': transaction})

