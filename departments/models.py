from django.db import models
from django.utils import timezone


class Department(models.Model):
    """
    Department model with hierarchical structure
    Supports unlimited nesting levels for organizational structure
    """
    
    DEPARTMENT_TYPE_CHOICES = [
        ('Division', 'Division'),
        ('Department', 'Department'),
        ('Team', 'Team'),
        ('Unit', 'Unit'),
    ]
    
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Department name (must be unique)"
    )
    
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Department code (e.g., IT, HR, FIN-ACC)"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of the department"
    )
    
    parent_department = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_departments',
        help_text="Parent department (NULL for top-level)"
    )
    
    department_type = models.CharField(
        max_length=20,
        choices=DEPARTMENT_TYPE_CHOICES,
        default='Department',
        help_text="Type of organizational unit"
    )
    
    head_of_department = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='departments_headed',
        help_text="Department head/manager"
    )
    
    cost_center = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Cost center code"
    )
    
    budget_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Budget allocation code"
    )
    
    office_location = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Physical office location"
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Department contact phone"
    )
    
    email = models.EmailField(
        blank=True,
        null=True,
        help_text="Department contact email"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this department is currently active"
    )
    
    established_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date when department was established"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='departments_created'
    )
    updated_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='departments_updated'
    )
    
    class Meta:
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def full_path(self):
        """Return the full hierarchical path of the department"""
        if self.parent_department:
            return f"{self.parent_department.full_path} → {self.name}"
        return self.name
    
    @property
    def level(self):
        """Return the nesting level of this department (0 for top-level)"""
        if not self.parent_department:
            return 0
        return self.parent_department.level + 1
    
    def get_all_sub_departments(self):
        """Get all sub-departments recursively"""
        sub_depts = list(self.sub_departments.all())
        for dept in self.sub_departments.all():
            sub_depts.extend(dept.get_all_sub_departments())
        return sub_depts
    
    def get_all_members(self):
        """Get all users in this department and its sub-departments"""
        from accounts.models import CustomUser
        
        # Get users directly in this department
        members = list(CustomUser.objects.filter(department=self))
        
        # Get users in all sub-departments
        for sub_dept in self.get_all_sub_departments():
            members.extend(CustomUser.objects.filter(department=sub_dept))
        
        return members
    
    def get_member_count(self):
        """Get total number of members in this department tree"""
        return len(self.get_all_members())
    
    def get_active_member_count(self):
        """Get number of active members in this department tree"""
        from accounts.models import CustomUser
        return CustomUser.objects.filter(
            department__in=[self] + self.get_all_sub_departments(),
            employment_status='Active',
            is_active=True
        ).count()
    
    def get_head_name(self):
        """Return department head's name or None"""
        return self.head_of_department.full_name if self.head_of_department else None
    
    def get_breadcrumb_path(self):
        """Return breadcrumb-style path for navigation"""
        path_parts = []
        current = self
        while current:
            path_parts.insert(0, current.name)
            current = current.parent_department
        return " → ".join(path_parts)
    
    def can_be_deleted(self):
        """Check if department can be safely deleted"""
        # Cannot delete if it has sub-departments
        if self.sub_departments.exists():
            return False, "Cannot delete department with sub-departments"
        
        # Cannot delete if it has active members
        if self.get_active_member_count() > 0:
            return False, "Cannot delete department with active members"
        
        return True, "Can be deleted"
    
    def move_to_department(self, new_parent):
        """Move this department to a new parent department"""
        # Prevent circular references
        if new_parent and (new_parent == self or new_parent.is_descendant_of(self)):
            raise ValueError("Cannot create circular department hierarchy")
        
        self.parent_department = new_parent
        self.save()
    
    def is_descendant_of(self, department):
        """Check if this department is a descendant of the given department"""
        current = self.parent_department
        while current:
            if current == department:
                return True
            current = current.parent_department
        return False
    
    def get_siblings(self):
        """Get all departments at the same level with the same parent"""
        if self.parent_department:
            return self.parent_department.sub_departments.exclude(id=self.id)
        return Department.objects.filter(parent_department=None).exclude(id=self.id)
