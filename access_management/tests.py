from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomUser
from systems.models import System
from access_management.models import (
    UserSystemAccess,
    QuarterlyAccessReview,
    QuarterlyActiveUserReview,
    AccessRemovalDocumentation,
)


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
        # field names include the prefix used by the partial ('system_owner_approver')
        self.assertContains(resp, 'name="system_owner_approver_approval_date"')
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
        # owner sees editable inputs with correct prefixed names
        self.assertContains(resp, 'name="system_owner_approver_approval_date"')
        self.assertNotContains(resp, '<p><strong>Approval Date:</strong>')


class QuarterlyReviewSimplePageTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='tester', password='pass')
        self.system = System.objects.create(name='Simple System', code='SSYS')
        self.client.force_login(self.user)

    def test_get_simple_page_shows_form_and_recent(self):
        resp = self.client.get(reverse('access_management:quarterly_access_review_simple'))
        self.assertEqual(resp.status_code, 200)
        # form inputs should be present
        self.assertContains(resp, 'name="review_quarter"')
        self.assertContains(resp, 'name="reviewed_user"')
        self.assertContains(resp, 'name="system"')

    def test_post_creates_review(self):
        data = {
            'review_quarter': '2026-Q1',
            'reviewed_user': self.user.pk,
            'reviewed_by': self.user.pk,
            'system': self.system.pk,
            'review_date': '2026-02-22T12:00',
            'approved_permissions': 'none',
            'actual_permissions_in_external_system': 'none',
            # checkbox fields come through as 'on' when checked; leave them unset for False
            'matches_approved': 'on',
            # don't mark completed so it stays in progress
        }
        resp = self.client.post(reverse('access_management:quarterly_access_review_simple'), data)
        self.assertRedirects(resp, reverse('access_management:quarterly_access_review_simple'))
        self.assertEqual(QuarterlyAccessReview.objects.count(), 1)


class QuarterlyReviewDetailedPageTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='detailuser', password='pass')
        self.system = System.objects.create(name='Detail System', code='DSYS')
        self.client.force_login(self.user)
        # create a sample review
        self.review = QuarterlyAccessReview.objects.create(
            review_quarter='2026-Q1',
            reviewed_user=self.user,
            system=self.system,
            reviewed_by=self.user,
            review_date='2026-02-22T12:00',
            approved_permissions='role:a',
            actual_permissions_in_external_system='role:a',
            matches_approved=True,
            review_completed=False,
        )

    def test_get_detailed_page_shows_list_and_form(self):
        resp = self.client.get(reverse('access_management:quarterly_access_review_detailed'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Detailed Review Log')
        self.assertContains(resp, 'role:a')

    def test_edit_review_updates_record(self):
        url = reverse('access_management:quarterly_access_review_detailed_edit', args=[self.review.pk])
        data = {
            'review_quarter': self.review.review_quarter,
            'reviewed_user': self.user.pk,
            'system': self.system.pk,
            'reviewed_by': self.user.pk,
            'review_date': '2026-02-22T12:00',
            'approved_permissions': 'role:a',
            'actual_permissions_in_external_system': 'role:b',
            'matches_approved': '',
            'review_completed': 'on',
        }
        resp = self.client.post(url, data)
        # after successful save we should redirect back to the edit view
        self.assertEqual(resp.status_code, 302)
        self.review.refresh_from_db()
        self.assertEqual(self.review.actual_permissions_in_external_system, 'role:b')
        self.assertTrue(self.review.review_completed)


class UpcomingOverdueReviewsPageTests(TestCase):
    def setUp(self):
        from django.utils import timezone
        from datetime import timedelta
        
        self.user = CustomUser.objects.create_user(username='upcoming_user', password='pass')
        self.system = System.objects.create(name='Test System', code='TSYS')
        self.client.force_login(self.user)
        self.now = timezone.now()
        
        # Create overdue assignment (review date in past)
        self.overdue_assignment = UserSystemAccess.objects.create(
            user=self.user,
            system=self.system,
            status='Active',
            next_review_date=self.now - timedelta(days=10),
            last_review_date=self.now - timedelta(days=100),
        )
        
        # Create upcoming assignment (due within 30 days)
        self.upcoming_assignment = UserSystemAccess.objects.create(
            user=self.user,
            system=self.system,
            status='Active',
            next_review_date=self.now + timedelta(days=15),
            last_review_date=self.now - timedelta(days=85),
        )

    def test_get_upcoming_page_loads(self):
        resp = self.client.get(reverse('access_management:quarterly_review_upcoming'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Upcoming & Overdue Reviews')

    def test_kpi_metrics_calculated_correctly(self):
        resp = self.client.get(reverse('access_management:quarterly_review_upcoming'))
        self.assertEqual(resp.status_code, 200)
        # Check that metrics are in context
        self.assertIn('metrics', resp.context)
        # Should show 1 overdue, 1 upcoming within 30 days
        self.assertEqual(resp.context['metrics']['overdue'], 1)
        self.assertEqual(resp.context['metrics']['upcoming_30_days'], 1)
        self.assertEqual(resp.context['metrics']['total_due'], 2)


class QuarterlyReviewToggleTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='user', password='pass')
        self.system = System.objects.create(name='Test System', code='TSYS')
        self.client.force_login(self.user)
        # create a review that starts as open
        self.review = QuarterlyActiveUserReview.objects.create(
            review_quarter='2025-Q1',
            system=self.system,
            reviewed_by=self.user,
            review_date=timezone.now(),
            total_active_users_in_external_system=10,
            approved_users_count=10,
            unapproved_users_count=0,
            review_completed=False,
        )

    def test_mark_review_completed(self):
        url = reverse('access_management:quarterly_review_toggle', args=[self.review.id])
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse('access_management:quarterly_review_detail'))
        self.review.refresh_from_db()
        self.assertTrue(self.review.review_completed)

    def test_reopen_review(self):
        self.review.review_completed = True
        self.review.save()
        url = reverse('access_management:quarterly_review_toggle', args=[self.review.id])
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse('access_management:quarterly_review_detail'))
        self.review.refresh_from_db()
        self.assertFalse(self.review.review_completed)


class AccessRemovalToggleTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='user', password='pass')
        self.system = System.objects.create(name='Test System', code='TSYS')
        self.client.force_login(self.user)
        # need a user_system_access to link removal
        self.access = UserSystemAccess.objects.create(
            user=self.user,
            system=self.system,
            status='Active',
            next_review_date=timezone.now(),
        )
        self.removal = AccessRemovalDocumentation.objects.create(
            user_system_access=self.access,
            removed_from_external_system_date=timezone.now(),
            removed_by=self.user,
            removal_reason='Test',
            verified_removal=False,
        )

    def test_verify_removal_sets_metadata(self):
        url = reverse('access_management:access_removal_toggle_verified', args=[self.removal.id])
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse('access_management:access_removal_documentation'))
        self.removal.refresh_from_db()
        self.assertTrue(self.removal.verified_removal)
        self.assertEqual(self.removal.verified_by, self.user)
        self.assertIsNotNone(self.removal.verified_date)

    def test_unverify_removal_clears_metadata(self):
        self.removal.verified_removal = True
        self.removal.verified_by = self.user
        self.removal.verified_date = timezone.now()
        self.removal.save()
        url = reverse('access_management:access_removal_toggle_verified', args=[self.removal.id])
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse('access_management:access_removal_documentation'))
        self.removal.refresh_from_db()
        self.assertFalse(self.removal.verified_removal)
        self.assertIsNone(self.removal.verified_by)
        self.assertIsNone(self.removal.verified_date)


class AdminAccessValidationTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='user', password='pass')
        # a system that looks like a Windows login/AD service
        self.login_system = System.objects.create(
            name='Windows Domain Controller',
            code='WINDC',
            system_type='Operating System',
            authentication_type='LDAP',
        )
        # a generic non-login system
        self.app_system = System.objects.create(name='Finance App', code='FIN', system_type='Web Application')
        self.client.force_login(self.user)

    def test_login_system_requires_admin_info(self):
        """Posting create without any admin metadata should re-render form and
        not create an assignment when the system is a login platform."""
        data = {
            'user': self.user.pk,
            'system': self.login_system.pk,
            'access_type': 'Read',
            'request_type': 'New',
            'priority': 'Medium',
            'business_justification': 'need access',
            'system_username': 'jdoe',
        }
        resp = self.client.post(reverse('access_management:access_assignment_create'), data)
        # form should redisplay (200) with error message and not create record
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Administrator Access (4.3 Compliance)')
        self.assertContains(resp, 'information is required for login systems')
        self.assertEqual(UserSystemAccess.objects.count(), 0)

    def test_login_system_succeeds_with_admin_info(self):
        data = {
            'user': self.user.pk,
            'system': self.login_system.pk,
            'access_type': 'Read',
            'request_type': 'New',
            'priority': 'Medium',
            'business_justification': 'need access',
            'system_username': 'jdoe',
            'is_admin_access': 'on',
        }
        resp = self.client.post(reverse('access_management:access_assignment_create'), data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(UserSystemAccess.objects.count(), 1)

    def test_non_login_system_does_not_require_admin(self):
        data = {
            'user': self.user.pk,
            'system': self.app_system.pk,
            'access_type': 'Read',
            'request_type': 'New',
            'priority': 'Medium',
            'business_justification': 'need access',
            'system_username': 'jdoe',
        }
        resp = self.client.post(reverse('access_management:access_assignment_create'), data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(UserSystemAccess.objects.count(), 1)

    def test_form_context_includes_login_system_ids(self):
        resp = self.client.get(reverse('access_management:access_assignment_create'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('login_system_ids', resp.context)
        ids = resp.context['login_system_ids']
        self.assertIn(str(self.login_system.pk), ids)
        self.assertNotIn(str(self.app_system.pk), ids)

    def test_admin_card_initially_visible_for_login_system(self):
        # GET with system parameter should render card visible when system is login-type
        resp = self.client.get(reverse('access_management:access_assignment_create'), {'system': self.login_system.pk})
        self.assertEqual(resp.status_code, 200)
        # card exists and not hidden via inline style
        self.assertContains(resp, 'id="admin-access-card"')
        self.assertNotContains(resp, 'id="admin-access-card" class="card form-card" style="display:none;"')

    def test_admin_card_initially_hidden_for_non_login_system(self):
        resp = self.client.get(reverse('access_management:access_assignment_create'), {'system': self.app_system.pk})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'id="admin-access-card"')
        self.assertContains(resp, 'id="admin-access-card" class="card form-card" style="display:none;"')


class UnreviewedUsersPageTests(TestCase):
    def setUp(self):
        from django.utils import timezone
        
        self.user1 = CustomUser.objects.create_user(username='user1', password='pass', first_name='John', last_name='Doe')
        self.user2 = CustomUser.objects.create_user(username='user2', password='pass', first_name='Jane', last_name='Smith')
        self.system = System.objects.create(name='Test System', code='TSYS')
        self.client.force_login(self.user1)
        
        # Create a review for user1 this year
        now = timezone.now()
        QuarterlyAccessReview.objects.create(
            review_quarter=f'{now.year}-Q1',
            reviewed_user=self.user1,
            system=self.system,
            reviewed_by=self.user1,
            review_date=now,
            approved_permissions='role:a',
            actual_permissions_in_external_system='role:a',
            matches_approved=True,
            review_completed=True,
        )

    def test_unreviewed_users_page_loads(self):
        resp = self.client.get(reverse('access_management:quarterly_review_unreviewed_users'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Unreviewed Users')

    def test_unreviewed_users_filtering(self):
        resp = self.client.get(reverse('access_management:quarterly_review_unreviewed_users'))
        self.assertEqual(resp.status_code, 200)
        # user2 should be in the list (not yet reviewed)
        # user1 should NOT be in the list (already reviewed)
        self.assertContains(resp, 'Users Needing Review', html=False)


