"""
LDAP Authentication Backend for User Access Management System
Supports both Active Directory and generic LDAP servers
"""
import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from ldap3 import Server, Connection, ALL, NTLM, SIMPLE, Tls, SUBTREE
from ldap3.core.exceptions import LDAPException, LDAPBindError
import ssl
from .models import LDAPConfiguration

logger = logging.getLogger(__name__)
User = get_user_model()


class LDAPAuthenticationBackend(ModelBackend):
    """
    Custom LDAP authentication backend with comprehensive AD/LDAP support
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user against LDAP/AD server
        """
        if not username or not password:
            return None
        
        # Get active LDAP configuration
        ldap_config = LDAPConfiguration.get_active_config()
        if not ldap_config or not ldap_config.ldap_enabled:
            logger.debug("LDAP authentication is not enabled")
            return None
        
        try:
            # Authenticate with LDAP
            ldap_user_data = self._ldap_authenticate(username, password, ldap_config)
            if not ldap_user_data:
                return None
            
            # Get or create user in Django
            user = self._get_or_create_user(username, ldap_user_data, ldap_config)
            
            # Update user with LDAP data
            if user:
                self._update_user_from_ldap(user, ldap_user_data, ldap_config, password)
            
            return user
            
        except Exception as e:
            logger.error(f"LDAP authentication error: {str(e)}")
            return None
    
    def _ldap_authenticate(self, username, password, ldap_config):
        """
        Authenticate user against LDAP server and retrieve user attributes
        """
        try:
            # Setup TLS if needed
            tls_config = None
            if ldap_config.use_tls or ldap_config.ldap_server.startswith('ldaps://'):
                tls_config = Tls(
                    validate=ssl.CERT_REQUIRED if not ldap_config.allow_invalid_ssl else ssl.CERT_NONE,
                    version=ssl.PROTOCOL_TLSv1_2,
                    ca_certs_file=None,
                    valid_names=None
                )
            
            # Create LDAP server object
            server = Server(
                ldap_config.ldap_server,
                get_info=ALL,
                tls=tls_config,
                use_ssl=ldap_config.ldap_server.startswith('ldaps://')
            )
            
            # First, bind with service account to search for user
            bind_user = ldap_config.bind_username
            bind_password = ldap_config.get_bind_password()
            
            # Search for user DN
            user_dn = self._find_user_dn(
                server, bind_user, bind_password, username, ldap_config
            )
            
            if not user_dn:
                logger.warning(f"User {username} not found in LDAP")
                return None
            
            # Now authenticate as the user
            user_conn = Connection(
                server,
                user=user_dn,
                password=password,
                authentication=SIMPLE,
                auto_bind=True
            )
            
            # If we got here, authentication was successful
            # Now retrieve user attributes
            user_data = self._get_ldap_user_attributes(
                user_conn, user_dn, ldap_config
            )
            
            user_conn.unbind()
            return user_data
            
        except LDAPBindError as e:
            logger.warning(f"LDAP bind failed for user {username}: {str(e)}")
            return None
        except LDAPException as e:
            logger.error(f"LDAP error during authentication: {str(e)}")
            return None
    
    def _find_user_dn(self, server, bind_user, bind_password, username, ldap_config):
        """
        Find user's Distinguished Name (DN) in LDAP
        """
        try:
            # Bind with service account
            conn = Connection(
                server,
                user=bind_user,
                password=bind_password,
                authentication=SIMPLE,
                auto_bind=True
            )
            
            # Build search filter
            username_field = ldap_config.ldap_username_field or 'sAMAccountName'
            search_filter = f"(&{ldap_config.ldap_filter}({username_field}={username}))"
            
            # Search for user
            conn.search(
                search_base=ldap_config.base_dn,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=['distinguishedName', 'dn']
            )
            
            if conn.entries:
                user_dn = conn.entries[0].entry_dn
                conn.unbind()
                return user_dn
            
            conn.unbind()
            return None
            
        except Exception as e:
            logger.error(f"Error finding user DN: {str(e)}")
            return None
    
    def _get_ldap_user_attributes(self, conn, user_dn, ldap_config):
        """
        Retrieve user attributes from LDAP
        """
        # Build attribute list to retrieve
        attributes = [
            ldap_config.ldap_username_field or 'sAMAccountName',
            ldap_config.ldap_firstname_field or 'givenName',
            ldap_config.ldap_lastname_field or 'sn',
            ldap_config.ldap_email_field or 'mail',
            ldap_config.ldap_displayname_field or 'displayName',
            ldap_config.ldap_employeenumber_field or 'employeeNumber',
            ldap_config.ldap_department_field or 'department',
            ldap_config.ldap_manager_field or 'manager',
            ldap_config.ldap_phone_field or 'telephoneNumber',
            ldap_config.ldap_mobile_field or 'mobile',
            ldap_config.ldap_jobtitle_field or 'title',
            ldap_config.ldap_address_field or 'streetAddress',
            ldap_config.ldap_city_field or 'l',
            ldap_config.ldap_state_field or 'st',
            ldap_config.ldap_postalcode_field or 'postalCode',
            ldap_config.ldap_country_field or 'co',
            ldap_config.ldap_active_flag or 'userAccountControl',
            'distinguishedName'
        ]
        
        # Remove empty attributes
        attributes = [attr for attr in attributes if attr]
        
        try:
            # Search for user attributes
            conn.search(
                search_base=user_dn,
                search_filter='(objectClass=*)',
                search_scope=SUBTREE,
                attributes=attributes
            )
            
            if not conn.entries:
                return None
            
            entry = conn.entries[0]
            user_data = {}
            
            # Extract attributes
            for attr in attributes:
                if hasattr(entry, attr):
                    value = getattr(entry, attr).value
                    user_data[attr] = value
            
            return user_data
            
        except Exception as e:
            logger.error(f"Error retrieving LDAP attributes: {str(e)}")
            return None
    
    def _get_or_create_user(self, username, ldap_user_data, ldap_config):
        """
        Get existing user or create new one from LDAP data
        """
        def get_field(data, field):
            """Get field value case-insensitively"""
            return data.get(field) or data.get(field.lower()) or data.get(field.upper(), '')
        
        try:
            username_field = ldap_config.ldap_username_field or 'sAMAccountName'
            ldap_username = get_field(ldap_user_data, username_field) or username
            
            # Try to find user by username or email
            email_field = ldap_config.ldap_email_field or 'mail'
            email = get_field(ldap_user_data, email_field)
            
            # Try username first
            try:
                user = User.objects.get(username=ldap_username)
                return user
            except User.DoesNotExist:
                pass
            
            # Try email if available
            if email:
                try:
                    user = User.objects.get(email=email)
                    return user
                except User.DoesNotExist:
                    pass
            
            # Create new user
            firstname_field = ldap_config.ldap_firstname_field or 'givenName'
            lastname_field = ldap_config.ldap_lastname_field or 'sn'
            
            user = User.objects.create_user(
                username=ldap_username,
                email=email or '',
                first_name=get_field(ldap_user_data, firstname_field) or '',
                last_name=get_field(ldap_user_data, lastname_field) or '',
            )
            
            # Mark as AD synced
            user.ad_synced = True
            user.ad_username = ldap_username
            user.save()
            
            logger.info(f"Created new user from LDAP: {ldap_username}")
            return user
            
        except Exception as e:
            logger.error(f"Error getting or creating user: {str(e)}")
            return None
    
    def _update_user_from_ldap(self, user, ldap_user_data, ldap_config, password=None):
        """
        Update Django user with LDAP data
        """
        from django.utils import timezone
        from departments.models import Department
        
        def get_field(data, field):
            """Get field value case-insensitively"""
            return data.get(field) or data.get(field.lower()) or data.get(field.upper())
        
        try:
            # Update basic fields
            firstname_field = ldap_config.ldap_firstname_field or 'givenName'
            lastname_field = ldap_config.ldap_lastname_field or 'sn'
            email_field = ldap_config.ldap_email_field or 'mail'
            displayname_field = ldap_config.ldap_displayname_field or 'displayName'
            
            user.first_name = get_field(ldap_user_data, firstname_field) or user.first_name
            user.last_name = get_field(ldap_user_data, lastname_field) or user.last_name
            user.email = get_field(ldap_user_data, email_field) or user.email
            
            # Update extended fields if available (using case-insensitive lookup)
            phone_field = ldap_config.ldap_phone_field or 'telephoneNumber'
            mobile_field = ldap_config.ldap_mobile_field or 'mobile'
            jobtitle_field = ldap_config.ldap_jobtitle_field or 'title'
            address_field = ldap_config.ldap_address_field or 'streetAddress'
            city_field = ldap_config.ldap_city_field or 'l'
            state_field = ldap_config.ldap_state_field or 'st'
            postalcode_field = ldap_config.ldap_postalcode_field or 'postalCode'
            country_field = ldap_config.ldap_country_field or 'co'
            department_field = ldap_config.ldap_department_field or 'department'
            
            # Phone
            phone_value = get_field(ldap_user_data, phone_field)
            if phone_value:
                phone = str(phone_value)
                if len(phone) >= 7:  # Basic validation
                    user.phone_primary = phone
            
            # Mobile
            mobile_value = get_field(ldap_user_data, mobile_field)
            if mobile_value:
                user.phone_secondary = str(mobile_value)
            
            # Job Title / Position
            jobtitle_value = get_field(ldap_user_data, jobtitle_field)
            if jobtitle_value:
                user.position = str(jobtitle_value)
                user.job_title = str(jobtitle_value)
            
            # Description (from AD description field)
            description_value = get_field(ldap_user_data, 'description')
            if description_value:
                user.description = str(description_value)
            
            # Office Location (from physicalDeliveryOfficeName or office)
            office_value = get_field(ldap_user_data, 'physicalDeliveryOfficeName') or get_field(ldap_user_data, 'office')
            if office_value:
                user.office_location = str(office_value)
            
            # Company (can be used for notes or other field)
            company_value = get_field(ldap_user_data, 'company')
            if company_value and not user.notes:
                user.notes = f"Company: {company_value}"
            
            # Address fields
            address_value = get_field(ldap_user_data, address_field)
            if address_value:
                user.work_address = str(address_value)
            
            city_value = get_field(ldap_user_data, city_field)
            if city_value:
                user.city = str(city_value)
            
            state_value = get_field(ldap_user_data, state_field)
            if state_value:
                user.state_province = str(state_value)
            
            postalcode_value = get_field(ldap_user_data, postalcode_field)
            if postalcode_value:
                user.postal_code = str(postalcode_value)
            
            country_value = get_field(ldap_user_data, country_field)
            if country_value:
                user.country = str(country_value)
            
            # Employee Number / ID
            employee_field = ldap_config.ldap_employeenumber_field or 'employeeNumber'
            employee_value = get_field(ldap_user_data, employee_field) or get_field(ldap_user_data, 'employeeID')
            # Note: employee_id is auto-generated, so we store AD employee number in notes if different
            if employee_value and str(employee_value) != user.employee_id:
                if user.notes:
                    if 'AD Employee#' not in user.notes:
                        user.notes += f"\nAD Employee#: {employee_value}"
                else:
                    user.notes = f"AD Employee#: {employee_value}"
            
            # Update department
            dept_value = get_field(ldap_user_data, department_field)
            if dept_value:
                dept_name = str(dept_value)
                dept, created = Department.objects.get_or_create(
                    name=dept_name,
                    defaults={'description': f'Auto-created from LDAP sync'}
                )
                user.department = dept
            
            # Update AD sync fields
            user.ad_synced = True
            user.ad_username = user.username
            user.last_ad_sync = timezone.now()
            dn_value = get_field(ldap_user_data, 'distinguishedName')
            if dn_value:
                user.ad_distinguished_name = str(dn_value)
            
            # Check active flag (userAccountControl for AD)
            active_flag_field = ldap_config.ldap_active_flag or 'userAccountControl'
            active_value = get_field(ldap_user_data, active_flag_field)
            if active_value is not None:
                # For AD userAccountControl: bit 2 (value 2) means disabled
                # Normal active account has value like 512, 544, etc.
                # Disabled account has value like 514, 546, etc.
                if ldap_config.is_active_directory and active_flag_field.lower() == 'useraccountcontrol':
                    try:
                        uac_value = int(active_value)
                        is_disabled = (uac_value & 2) != 0
                        user.is_active = not is_disabled if not ldap_config.ldap_invert_active_flag else is_disabled
                    except (ValueError, TypeError):
                        pass
                else:
                    # Generic boolean check
                    is_active = bool(active_value) and str(active_value).lower() not in ['0', 'false', 'disabled']
                    user.is_active = not is_active if ldap_config.ldap_invert_active_flag else is_active
            
            # Cache password if enabled
            if ldap_config.cache_passwords and password:
                user.set_password(password)
            
            user.save()
            logger.info(f"Updated user {user.username} from LDAP")
            
        except Exception as e:
            logger.error(f"Error updating user from LDAP: {str(e)}")


class LDAPSync:
    """
    Utility class for syncing users from LDAP/AD
    """
    
    @staticmethod
    def sync_all_users(ldap_config=None, bind_password=None):
        """
        Sync all users from LDAP/AD directory.

        If bind_password is provided, it will be used only for this operation
        and not read from the database. If it is not provided, the method will
        fall back to the stored (encrypted) bind password for backwards
        compatibility.
        """
        if not ldap_config:
            ldap_config = LDAPConfiguration.get_active_config()

        if not ldap_config or not ldap_config.ldap_enabled:
            logger.warning("LDAP is not enabled, cannot sync users")
            return {'success': False, 'message': 'LDAP is not enabled'}

        # Prefer runtime bind_password when given; otherwise fall back
        password_to_use = bind_password or ldap_config.get_bind_password()
        if not password_to_use:
            logger.warning("No LDAP bind password provided for sync_all_users")
            return {
                'success': False,
                'message': 'Bind password is required for LDAP sync but was not provided.',
            }

        try:
            # Setup connection
            tls_config = None
            if ldap_config.use_tls or ldap_config.ldap_server.startswith('ldaps://'):
                tls_config = Tls(
                    validate=ssl.CERT_REQUIRED if not ldap_config.allow_invalid_ssl else ssl.CERT_NONE,
                    version=ssl.PROTOCOL_TLSv1_2
                )

            server = Server(
                ldap_config.ldap_server,
                get_info=ALL,
                tls=tls_config,
                use_ssl=ldap_config.ldap_server.startswith('ldaps://')
            )

            conn = Connection(
                server,
                user=ldap_config.bind_username,
                password=password_to_use,
                authentication=SIMPLE,
                auto_bind=True
            )

            # Search for all users
            conn.search(
                search_base=ldap_config.base_dn,
                search_filter=ldap_config.ldap_filter or '(&(objectClass=user)(objectCategory=person))',
                search_scope=SUBTREE,
                attributes='*'
            )

            synced_count = 0
            error_count = 0

            backend = LDAPAuthenticationBackend()

            for entry in conn.entries:
                try:
                    # Convert entry to dict (case-insensitive keys)
                    user_data = {}
                    for attr in entry.entry_attributes:
                        # Store both original and lowercase keys for compatibility
                        user_data[attr] = entry[attr].value
                        user_data[attr.lower()] = entry[attr].value

                    # Get username - try both cases
                    username_field = ldap_config.ldap_username_field or 'sAMAccountName'
                    username = (
                        user_data.get(username_field)
                        or user_data.get(username_field.lower())
                        or user_data.get('sAMAccountName')
                        or user_data.get('samaccountname', '')
                    )

                    # Skip computer accounts (end with $) and system accounts
                    if username and not username.endswith('$') and username.lower() not in ['krbtgt', 'guest']:
                        user = backend._get_or_create_user(username, user_data, ldap_config)
                        if user:
                            backend._update_user_from_ldap(user, user_data, ldap_config)
                            synced_count += 1
                except Exception as e:
                    logger.error(f"Error syncing user: {str(e)}")
                    error_count += 1

            conn.unbind()

            return {
                'success': True,
                'synced_count': synced_count,
                'error_count': error_count,
                'message': f'Synced {synced_count} users successfully, {error_count} errors'
            }

        except Exception as e:
            logger.error(f"Error during LDAP sync: {str(e)}")
            return {'success': False, 'message': str(e)}

    @staticmethod
    def test_connection(ldap_config, bind_password=None):
        """
        Test LDAP connection.

        If bind_password is provided, it will be used only for this operation
        and not read from the database. If it is not provided, the method will
        fall back to the stored (encrypted) bind password for backwards
        compatibility.
        """
        # Prefer runtime bind_password when given; otherwise fall back
        password_to_use = bind_password or ldap_config.get_bind_password()
        if not password_to_use:
            return {
                'success': False,
                'message': 'Bind password is required for LDAP connection test but was not provided.',
            }

        try:
            tls_config = None
            if ldap_config.use_tls or ldap_config.ldap_server.startswith('ldaps://'):
                tls_config = Tls(
                    validate=ssl.CERT_REQUIRED if not ldap_config.allow_invalid_ssl else ssl.CERT_NONE,
                    version=ssl.PROTOCOL_TLSv1_2
                )

            server = Server(
                ldap_config.ldap_server,
                get_info=ALL,
                tls=tls_config,
                use_ssl=ldap_config.ldap_server.startswith('ldaps://')
            )

            conn = Connection(
                server,
                user=ldap_config.bind_username,
                password=password_to_use,
                authentication=SIMPLE,
                auto_bind=True
            )

            conn.unbind()
            return {'success': True, 'message': 'LDAP connection successful'}

        except Exception as e:
            return {'success': False, 'message': f'Connection failed: {str(e)}'}


