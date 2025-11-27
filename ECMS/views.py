from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib import messages
from .models import Campaign, Recipient, DeliveryLog
from .forms import CampaignForm, RecipientUploadForm
import csv, io
from django.db import transaction

def campaign_list(request):
    qs = Campaign.objects.all().order_by('-created_at')
    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    campaigns_page = paginator.get_page(page)
    return render(request, 'ECMS/campaign_list.html', {'campaigns': campaigns_page})

def campaign_create(request):
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save()
            messages.success(request, "Campaign saved.")
            # schedule if scheduled_at present and status is scheduled
            if campaign.status == Campaign.STATUS_SCHEDULED and campaign.scheduled_at:
                from .tasks import schedule_campaign_send
                # If scheduled_at is in past or immediate, schedule right away
                if campaign.scheduled_at <= timezone.now():
                    schedule_campaign_send.delay(campaign.id)
                else:
                    schedule_campaign_send.apply_async((campaign.id,), eta=campaign.scheduled_at)
            return redirect('ECMS:campaign_list')
    else:
        form = CampaignForm()
    return render(request, 'ECMS/campaign_form.html', {'form': form})

def campaign_detail(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    logs_qs = DeliveryLog.objects.filter(campaign=campaign).order_by('-processed_at')
    paginator = Paginator(logs_qs, 25)
    page = request.GET.get('page')
    logs_page = paginator.get_page(page)
    return render(request, 'ECMS/campaign_detail.html', {'campaign': campaign, 'logs': logs_page})

def upload_recipients(request):
    if request.method == 'POST':
        form = RecipientUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            name_count = 0
            # Support csv and xlsx; simple path: csv only, else user can upload xlsx and we can extend with pandas/openpyxl
            if file.name.lower().endswith('.csv'):
                data = file.read().decode('utf-8')
                io_string = io.StringIO(data)
                reader = csv.DictReader(io_string) if ',' in io_string.getvalue().splitlines()[0] else csv.reader(io_string)
                created = 0
                to_create = []
                seen = set()
                from django.core.validators import validate_email
                from django.core.exceptions import ValidationError

                # If DictReader (header present)
                if isinstance(reader, csv.DictReader):
                    rows = reader
                else:
                    # fallback: assume simple rows name,email
                    rows = ({"name": r[0].strip(), "email": r[1].strip()} for r in reader if len(r) >= 2)

                for row in rows:
                    name = row.get('name','').strip()
                    email = row.get('email','').strip()
                    if not email:
                        continue
                    if email in seen:
                        continue
                    seen.add(email)
                    try:
                        validate_email(email)
                    except ValidationError:
                        continue
                    to_create.append(Recipient(name=name, email=email, status=Recipient.SUBSCRIBED))

                # Bulk insert in batches
                BATCH = 1000
                with transaction.atomic():
                    for i in range(0, len(to_create), BATCH):
                        batch = to_create[i:i+BATCH]
                        objs = Recipient.objects.bulk_create(batch, ignore_conflicts=True)
                        created += len(objs)

                messages.success(request, f'Inserted {created} recipients.')
                return redirect('ECMS:campaign_list')
            else:
                messages.error(request, "Only CSV supported in this uploader. Upload .csv for now.")
                return redirect('ECMS:upload_recipients')
    else:
        form = RecipientUploadForm()
    return render(request, 'ECMS/upload_recipients.html', {'form': form})

def send_campaign(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    # set scheduled now and schedule task immediately
    campaign.scheduled_at = timezone.now()
    campaign.status = Campaign.STATUS_SCHEDULED
    campaign.save(update_fields=['scheduled_at','status'])
    from .tasks import schedule_campaign_send
    schedule_campaign_send.delay(campaign.id)
    messages.success(request, "Campaign queued for sending.")
    return redirect('ECMS:campaign_detail', pk=pk)
