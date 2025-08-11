from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal


class AuditBase(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        related_name="%(class)s_created",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        User,
        related_name="%(class)s_updated",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class PersonBase(models.Model):
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    full_name = models.CharField(max_length=150, null=False, blank=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        self.full_name = " ".join(parts)
        super().save(*args, **kwargs)


class Company(AuditBase):
    company_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=4, null=True, blank=True, unique=True)
    name = models.CharField(max_length=100, null=False, blank=False, unique=True)
    address = models.TextField(null=True, blank=True)
    contact_number = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    contact_person = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "company"
        verbose_name_plural = "Companies"

    def __str__(self):
        return f"{self.code} - {self.name}" if self.code else self.name
    

class Branch(AuditBase):
    branch_id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, null=False, on_delete=models.CASCADE)
    code = models.CharField(max_length=4, null=True, blank=True, unique=True)
    name = models.CharField(max_length=100, null=False, blank=False, unique=True)
    address = models.TextField(null=True, blank=True)
    contact_number = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    contact_person = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "branch"
        verbose_name_plural = "Branches"

    def __str__(self):
        return f"{self.code} - {self.name}" if self.code else self.name
    

class Color(AuditBase):
    color_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, null=False, blank=False, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "color"
        verbose_name = "Color"
        verbose_name_plural = "Colors"

    def __str__(self):
        return self.name
    

class Period(models.Model):

    NUMBER_OF_MONTHS = 60

    MONTHLY = 1
    QUARTERLY = 2
    SEMI_ANNUAL = 3
    ANNUAL = 4
    SPOT_CASH = 5

    PERIOD_CHOICES = (
        (MONTHLY, 'Monthly'),
        (QUARTERLY, 'Quarterly'),
        (SEMI_ANNUAL, 'Semi-Annual'),
        (ANNUAL, 'Annual'),
        (SPOT_CASH, 'Spot Cash'),
    )

    name = models.CharField(max_length=50, unique=True)  # e.g., 'Monthly', 'Annual', 'Lump Sum'
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "period"
        verbose_name = "Period"
        verbose_name_plural = "Periods"
        ordering = ['name']  # Optional: orders periods alphabetically

    def __str__(self):
        return self.name
    

class GeneralSettings(AuditBase):
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='general_settings')
    grace_period_days = models.PositiveIntegerField(
        default=90,
        help_text="Days after due date before plan lapses (Default: 90 days)."
    )
    cutoff_day = models.PositiveSmallIntegerField(
        help_text="Day of the month billing is due (e.g., 5 = 5th of each month)."
    )
    contestability_months = models.PositiveSmallIntegerField(
        default=10,
        help_text="Months within which natural death is contestable. Accidental death is always covered."
    )
    waiting_period_years = models.PositiveSmallIntegerField(
        default=5,
        help_text="Years of payment before withdrawal eligibility. After 5 more years, 100% can be withdrawn."
    )
    system_timezone = models.CharField(
        max_length=100,
        default='Asia/Manila',
        help_text="Timezone for logs and transactions. (Default: Asia/Manila)"
    )

    class Meta:
        db_table = "general_settings"
        verbose_name = "General Setting"
        verbose_name_plural = "General Settings"

    def __str__(self):
        return f"Settings for {self.company.name}"
    

class Personnel(PersonBase, AuditBase):
    personnel_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=50, null=True, blank=True)
    company_name = models.CharField(max_length=150, null=True, blank=True)
    contact_number = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField()
    is_agent = models.BooleanField(default=False)
    is_collector = models.BooleanField(default=False)
    is_employee = models.BooleanField(default=False) 
    is_active = models.BooleanField(default=True)
    
 
    parent_personnel = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True,                
        blank=True,               
        related_name='children' 
    )

    class Meta:
        db_table = "personnel"
        verbose_name = "Personnel"
        verbose_name_plural = "Personnel"

    def __str__(self):
        # Assuming full_name comes from your PersonBase model
        return self.full_name


class Plan(AuditBase):
    plan_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150, null=False, blank=False, unique=True)
    description = models.TextField(null=True, blank=True)
    contract_price = models.FloatField(null=False, blank=False, default=0.00)
    rate = models.FloatField(null=False, blank=False, default=0.00)
    production = models.FloatField(null=False, blank=False, default=0.00)
    commission = models.FloatField(null=False, blank=False, default=0.00)
    allowance = models.FloatField(null=False, blank=False, default=0.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "plan"
        verbose_name = "Plan"
        verbose_name_plural = "Plans"

    def __str__(self):
        return self.name
    

class PlanPayment(AuditBase):
    payment_id = models.AutoField(primary_key=True)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="payments")
    period = models.ForeignKey(Period, on_delete=models.CASCADE, related_name="plan_payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # store payment amount

    class Meta:
        db_table = "plan_payment"
        verbose_name = "Plan Payment"
        verbose_name_plural = "Plan Payments"
        unique_together = ('plan', 'period')  # prevent duplicate entries

    def __str__(self):
        return f"{self.plan.name} - {self.period.name}: {self.amount}"
    

class Client(PersonBase, AuditBase):
    client_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=50, null=True, blank=True)
    birth_date = models.DateField(null=False, blank=False)
    address = models.TextField()
    
    gender = models.CharField(
        max_length=1,
        choices=[("M", "Male"), ("F", "Female")],
        default="M",
        help_text="Gender"
    )
    contact_number = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    civil_status = models.CharField(
        max_length=10,
        choices=[
            ("Single", "Single"),
            ("Married", "Married"),
            ("Widowed", "Widowed"),
            ("Divorced", "Divorced"),
        ],
        default="Single",
        null=True,
        blank=True,
        help_text="Civil Status"
    )
    occupation = models.CharField(max_length=100, null=True, blank=True)
    citizenship = models.CharField(max_length=100, null=True, blank=True)
    
    age = models.IntegerField(null=True, blank=True)

   

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "client"
        verbose_name = "Client"
        verbose_name_plural = "Clients"

    def __str__(self):
        return self.full_name
    

class ClientPlanStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    LAPSED = "lapsed", "Lapsed"
    REINSTATED = "reinstated", "Reinstated"
    TRANSFERRED = "transferred", "Transferred"
    ASSIGNED = "assigned", "Assigned"
    CANCELLED = "cancelled", "Cancelled"
    COMPLETED = "completed", "Completed"


class ClientPlan(AuditBase):
    client_plan_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(Client, null=False, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, null=False, default=1, on_delete=models.PROTECT)
    agent = models.ForeignKey(Personnel, null=True, blank=True, on_delete=models.SET_NULL, related_name="client_plans_as_agent", limit_choices_to={"is_agent": True})
    collector = models.ForeignKey(Personnel, null=True, blank=True, on_delete=models.SET_NULL, related_name="client_plans_as_collector", limit_choices_to={"is_collector": True})
    color = models.ForeignKey(Color, null=False, default=1, on_delete=models.PROTECT)
    branch = models.ForeignKey(Branch, on_delete=models.DO_NOTHING, null=True, blank=True, default=1, related_name="clients")
    contract_no = models.CharField(max_length=50, null=False, blank=False, unique=True)
    application_date = models.DateField(null=False, blank=False)
    effective_date = models.DateField(null=False, blank=False)
    period = models.ForeignKey(Period, null=False, default=1, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=ClientPlanStatus.choices, default=ClientPlanStatus.ACTIVE)
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    contestability_months = models.PositiveIntegerField(default=10)
    months_paid_continuously = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.contract_no} = {self.client.full_name} ({self.plan.name})"
    
    @property
    def is_contestable(self):
        return self.months_paid_continuously < self.contestability_months

    

class ClientBeneficiary(PersonBase, AuditBase):
    client_beneficiary_id = models.AutoField(primary_key=True)

    client_plan = models.ForeignKey(
        ClientPlan,
        null=False,
        on_delete=models.CASCADE,
        related_name='beneficiaries'
    )

    birth_date = models.DateField(null=False, blank=False)

    gender = models.CharField(
        max_length=1,
        choices=[("M", "Male"), ("F", "Female")],
        default="M",
        help_text="Gender"
    )

    age = models.IntegerField(
        null=True,
        blank=True,
        help_text="Age of the beneficiary at the time of registration (calculated via JavaScript)."
    )

    is_primary = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "client_beneficiary"
        verbose_name = "Client Beneficiary"
        verbose_name_plural = "Client Beneficiaries"
        constraints = [
            models.UniqueConstraint(
                fields=['client_plan', 'is_primary', 'is_active'],
                condition=models.Q(is_primary=True, is_active=True),
                name='unique_active_primary_per_client_plan'
            )
        ]

    def clean(self):
        # Run only when saving an active record
        if self.is_active:
            # Count other active beneficiaries for this plan (excluding self when updating)
            existing_active = ClientBeneficiary.objects.filter(
                client_plan=self.client_plan,
                is_active=True
            ).exclude(pk=self.pk)

            if existing_active.count() >= 2:
                raise ValidationError("A Client Plan can only have a maximum of 2 active beneficiaries.")

        # Optional: Warn if trying to mark two as primary
        if self.is_active and self.is_primary:
            existing_primary = ClientBeneficiary.objects.filter(
                client_plan=self.client_plan,
                is_primary=True,
                is_active=True
            ).exclude(pk=self.pk)

            if existing_primary.exists():
                raise ValidationError("There can only be one active primary beneficiary for a Client Plan.")

    def __str__(self):
        return f"{self.first_name} {self.last_name} (Beneficiary of {self.client_plan.client.full_name})"
    

class ClientPlanReinstatement(models.Model):
    client_plan = models.ForeignKey(ClientPlan, on_delete=models.CASCADE, related_name="reinstatements")
    reinstatement_date = models.DateField()
    previous_effective_date = models.DateField()
    new_effective_date = models.DateField()
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ClientPlanLapse(models.Model):
    client_plan = models.ForeignKey(ClientPlan, on_delete=models.CASCADE, related_name="lapses")
    lapse_date = models.DateField()
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ClientPlanTransfer(models.Model):
    from_client_plan = models.ForeignKey(ClientPlan, on_delete=models.CASCADE, related_name="transfers_made")
    to_client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="transferred_plans")
    transfer_date = models.DateField()
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)




