from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import DatabaseError
from .models import Import, ImportRow
from .forms import ImportForm

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
                messages.success(request, f'Import file uploaded successfully. Processing...')
                return redirect('import_detail', pk=import_obj.pk)
            except DatabaseError as e:
                messages.error(request, 'An error occurred while saving the import. Please try again.')
    else:
        form = ImportForm(user=request.user)
    return render(request, 'imports/import_new.html', {'form': form})

@login_required
def import_detail(request, pk):
    import_obj = get_object_or_404(Import, pk=pk, user=request.user)
    rows = ImportRow.objects.filter(import_obj=import_obj).order_by('-created_at')[:50]
    context = {
        'import_obj': import_obj,
        'rows': rows,
    }
    return render(request, 'imports/import_detail.html', context)

