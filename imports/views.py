from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import DatabaseError, transaction
from .models import Import, ImportRow
from .forms import ImportForm
from .services.ofx_parser import OFXParser
from .services.duplicate_detector import DuplicateDetector
from finance.models import Transaction, Category, Tag

@login_required
def import_list(request):
    imports = Import.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'imports/import_list.html', {'imports': imports})

@login_required
def import_new(request):
    if request.method == 'POST':
        form = ImportForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                import_obj = form.save(commit=False)
                import_obj.user = request.user
                import_obj.save()
                
                # Parse OFX file immediately if it's an OFX import
                if import_obj.type == 'ofx':
                    try:
                        parser = OFXParser(import_obj)
                        parser.parse()
                        messages.success(request, 'Arquivo OFX processado com sucesso. Revise os dados antes de confirmar a importação.')
                        return redirect('import_preview', pk=import_obj.pk)
                    except Exception as e:
                        import_obj.status = 'failed'
                        import_obj.error = str(e)
                        import_obj.save(update_fields=['status', 'error'])
                        messages.error(request, f'Erro ao processar arquivo OFX: {str(e)}')
                        return render(request, 'imports/import_new.html', {'form': form})
                else:
                    # For CSV, redirect to detail page (CSV parsing might be handled differently)
                    messages.success(request, f'Import file uploaded successfully. Processing...')
                    return redirect('import_detail', pk=import_obj.pk)
            except DatabaseError as e:
                messages.error(request, 'An error occurred while saving the import. Please try again.')
    else:
        form = ImportForm(user=request.user)
    return render(request, 'imports/import_new.html', {'form': form})

@login_required
def import_preview(request, pk):
    """Preview parsed import rows before confirming import"""
    import_obj = get_object_or_404(Import, pk=pk, user=request.user)
    rows = ImportRow.objects.filter(import_obj=import_obj).order_by('-date', '-created_at')
    context = {
        'import_obj': import_obj,
        'rows': rows,
    }
    return render(request, 'imports/import_preview.html', context)

@login_required
def import_confirm(request, pk):
    """Process import and create transactions from ImportRow objects"""
    import_obj = get_object_or_404(Import, pk=pk, user=request.user)
    
    if request.method != 'POST':
        return redirect('import_preview', pk=import_obj.pk)
    
    try:
        # Get all rows for this import
        rows = list(ImportRow.objects.filter(import_obj=import_obj))
        
        if not rows:
            messages.error(request, 'Nenhuma transação encontrada para importar.')
            return redirect('import_preview', pk=import_obj.pk)
        
        # Detect duplicates
        detector = DuplicateDetector(import_obj.user, import_obj.account)
        duplicates = detector.detect_duplicates(rows)
        
        # Mark duplicates
        for row in duplicates:
            row.status = 'duplicate'
            row.save(update_fields=['status'])
        
        import_obj.duplicate_rows = len(duplicates)
        import_obj.status = 'processing'
        import_obj.save(update_fields=['duplicate_rows', 'status'])
        
        # Import non-duplicate rows
        imported_count = 0
        error_count = 0
        
        with transaction.atomic():
            for row in rows:
                if row.status == 'duplicate':
                    continue
                
                if not row.date or not row.amount:
                    row.status = 'error'
                    row.error_message = 'Missing date or amount'
                    row.save(update_fields=['status', 'error_message'])
                    error_count += 1
                    continue
                
                try:
                    # Ensure amount is positive (Transaction model requires positive amounts)
                    # Store absolute value - income/expense is determined by category classification
                    amount = abs(row.amount)
                    
                    # Create transaction
                    txn = Transaction.objects.create(
                        account=import_obj.account or _get_default_account(import_obj.user),
                        date=row.date,
                        amount=amount,
                        currency=row.currency or import_obj.currency,
                        name=row.name,
                        notes=row.notes,
                    )
                    
                    # Set category if provided
                    if row.category:
                        category = _get_or_create_category(import_obj.user, row.category)
                        txn.category = category
                        txn.save(update_fields=['category'])
                    
                    # Set tags if provided
                    if row.tags:
                        _set_tags(import_obj.user, txn, row.tags)
                    
                    row.status = 'imported'
                    row.save(update_fields=['status'])
                    imported_count += 1
                    
                except Exception as e:
                    row.status = 'error'
                    row.error_message = str(e)
                    row.save(update_fields=['status', 'error_message'])
                    error_count += 1
        
        import_obj.status = 'completed'
        import_obj.imported_rows = imported_count
        import_obj.error_rows = error_count
        import_obj.save(update_fields=['status', 'imported_rows', 'error_rows'])
        
        messages.success(request, f'Importação concluída! {imported_count} transações importadas com sucesso.')
        return redirect('transaction_list')
        
    except Exception as e:
        import_obj.status = 'failed'
        import_obj.error = str(e)
        import_obj.save(update_fields=['status', 'error'])
        messages.error(request, f'Erro ao processar importação: {str(e)}')
        return redirect('import_preview', pk=import_obj.pk)

def _get_default_account(user):
    """Get default account for user"""
    from finance.models import Account
    return Account.objects.filter(user=user, status='active').first()

def _get_or_create_category(user, category_name: str) -> Category:
    """Get or create category"""
    category, _ = Category.objects.get_or_create(
        user=user,
        name=category_name,
        defaults={'classification': 'expense'}
    )
    return category

def _set_tags(user, transaction: Transaction, tags_str: str):
    """Set tags on transaction"""
    from finance.models import TransactionTag
    
    tag_names = [t.strip() for t in tags_str.split(',')]
    for tag_name in tag_names:
        if tag_name:
            tag, _ = Tag.objects.get_or_create(
                user=user,
                name=tag_name
            )
            TransactionTag.objects.get_or_create(
                transaction=transaction,
                tag=tag
            )

@login_required
def import_detail(request, pk):
    import_obj = get_object_or_404(Import, pk=pk, user=request.user)
    rows = ImportRow.objects.filter(import_obj=import_obj).order_by('-created_at')[:50]
    context = {
        'import_obj': import_obj,
        'rows': rows,
    }
    return render(request, 'imports/import_detail.html', context)

