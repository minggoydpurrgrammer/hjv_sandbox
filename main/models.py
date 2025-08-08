from django.conf import settings
from django.db import models
from django.contrib.auth.models import User


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
