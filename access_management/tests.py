from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from systems.models import System
from access_management.models import UserSystemAccess


class SystemOwnerSectionTests(TestCase):
    def setUp(self):
        # create a couple of users and a system
        self.user = CustomUser.objects.create_user(username='user1', password='pass')
        self.owner = CustomUser.objects.create_user(username='owner', password='pass')
        self.system = System.objects.create(name='Test System', code='TSYS', system_owner=self.owner)

    def test_create_form_shows_editable_owner_section(self):
        """On the new-access form the owner section should be editable by default."""
        self.client.force_login(self.user)
        resp = self.client.get(reverse('access_management:access_assignment_create'))
        self.assertEqual(resp.status_code, 200)
        # the approval date input should be present (editable form)
        self.assertContains(resp, 'name="system_owner_approval_date"')
        # when editing is allowed the partial renders inputs instead of plain text
        self.assertNotContains(resp, '<p><strong>Approval Date:</strong>')

    def test_update_form_readonly_when_not_owner(self):
        """A regular user who is not system owner sees a read‑only owner section."""
        assignment = UserSystemAccess.objects.create(
            user=self.user,
            system=self.system,
            business_justification='reason',
        )
        self.client.force_login(self.user)
        resp = self.client.get(reverse('access_management:access_assignment_update', args=[assignment.pk]))
        self.assertEqual(resp.status_code, 200)
        # owner section should render plain text rather than inputs
        self.assertNotContains(resp, 'name="system_owner_approval_date"')
        self.assertContains(resp, '<p><strong>Approval Date:</strong>')

    def test_update_form_editable_for_system_owner(self):
        """The system owner (or staff) should be able to edit owner fields."""
        assignment = UserSystemAccess.objects.create(
            user=self.user,
            system=self.system,
            business_justification='reason',
        )
        # owner user logs in
        self.client.force_login(self.owner)
        resp = self.client.get(reverse('access_management:access_assignment_update', args=[assignment.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'name="system_owner_approval_date"')
        self.assertNotContains(resp, '<p><strong>Approval Date:</strong>')
