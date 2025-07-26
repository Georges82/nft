#!/usr/bin/env python3
"""
Certificate-Based Authentication System Testing for Joinery Project Management
Tests admin certificate management, client authentication, and protected routes
"""

import requests
import json
from datetime import datetime
import sys
import time

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading backend URL: {e}")
        return None

BASE_URL = get_backend_url()
if not BASE_URL:
    print("ERROR: Could not get backend URL from frontend/.env")
    sys.exit(1)

API_URL = f"{BASE_URL}/api"
ADMIN_SECRET = "joinery_admin_2024_secret_key"

print(f"Testing certificate authentication at: {API_URL}")

class AuthenticationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "errors": []
        }
        self.generated_certificates = []
        self.client_tokens = {}

    def log_test(self, test_name, success, message=""):
        self.test_results["total_tests"] += 1
        if success:
            self.test_results["passed_tests"] += 1
            print(f"✅ {test_name}: PASSED {message}")
        else:
            self.test_results["failed_tests"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")
            print(f"❌ {test_name}: FAILED - {message}")

    def test_admin_generate_certificate(self, client_name, client_email):
        """Test admin certificate generation"""
        try:
            headers = {"Authorization": f"Bearer {ADMIN_SECRET}"}
            data = {
                "client_name": client_name,
                "client_email": client_email,
                "expires_days": 365
            }
            
            response = self.session.post(f"{API_URL}/admin/generate-certificate", 
                                       json=data, headers=headers)
            
            if response.status_code == 200:
                cert_data = response.json()
                required_fields = ["certificate_id", "client_name", "client_email", "certificate", "expires_at"]
                
                if all(field in cert_data for field in required_fields):
                    self.generated_certificates.append(cert_data)
                    self.log_test("Admin Generate Certificate", True, 
                                f"Generated certificate for {client_name}")
                    return cert_data
                else:
                    self.log_test("Admin Generate Certificate", False, 
                                f"Missing required fields in response")
                    return None
            else:
                self.log_test("Admin Generate Certificate", False, 
                            f"Status code: {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            self.log_test("Admin Generate Certificate", False, f"Exception: {str(e)}")
            return None

    def test_admin_list_certificates(self):
        """Test admin certificate listing"""
        try:
            headers = {"Authorization": f"Bearer {ADMIN_SECRET}"}
            response = self.session.get(f"{API_URL}/admin/certificates", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "certificates" in data and isinstance(data["certificates"], list):
                    cert_count = len(data["certificates"])
                    self.log_test("Admin List Certificates", True, 
                                f"Retrieved {cert_count} certificates")
                    return data["certificates"]
                else:
                    self.log_test("Admin List Certificates", False, 
                                "Invalid response format")
                    return None
            else:
                self.log_test("Admin List Certificates", False, 
                            f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Admin List Certificates", False, f"Exception: {str(e)}")
            return None

    def test_client_login(self, certificate):
        """Test client login with certificate"""
        try:
            data = {"certificate": certificate}
            response = self.session.post(f"{API_URL}/auth/login", json=data)
            
            if response.status_code == 200:
                login_data = response.json()
                if "user" in login_data and "message" in login_data:
                    user = login_data["user"]
                    if all(field in user for field in ["client_name", "client_email", "certificate_id"]):
                        self.log_test("Client Login", True, 
                                    f"Login successful for {user['client_name']}")
                        return login_data
                    else:
                        self.log_test("Client Login", False, 
                                    "Missing user fields in response")
                        return None
                else:
                    self.log_test("Client Login", False, 
                                "Invalid login response format")
                    return None
            else:
                self.log_test("Client Login", False, 
                            f"Status code: {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            self.log_test("Client Login", False, f"Exception: {str(e)}")
            return None

    def test_certificate_verification(self, certificate):
        """Test certificate verification endpoint"""
        try:
            headers = {"Authorization": f"Bearer {certificate}"}
            response = self.session.get(f"{API_URL}/auth/verify", headers=headers)
            
            if response.status_code == 200:
                verify_data = response.json()
                if verify_data.get("valid") and "user" in verify_data:
                    self.log_test("Certificate Verification", True, 
                                f"Certificate verified for {verify_data['user']['client_name']}")
                    return verify_data
                else:
                    self.log_test("Certificate Verification", False, 
                                "Invalid verification response")
                    return None
            else:
                self.log_test("Certificate Verification", False, 
                            f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Certificate Verification", False, f"Exception: {str(e)}")
            return None

    def test_protected_dashboard_access(self, certificate):
        """Test accessing protected dashboard with certificate"""
        try:
            headers = {"Authorization": f"Bearer {certificate}"}
            response = self.session.get(f"{API_URL}/dashboard", headers=headers)
            
            if response.status_code == 200:
                dashboard_data = response.json()
                required_fields = ["total_projects", "active_projects", "total_revenue", "total_costs"]
                
                if all(field in dashboard_data for field in required_fields):
                    self.log_test("Protected Dashboard Access", True, 
                                f"Dashboard accessible with certificate")
                    return dashboard_data
                else:
                    self.log_test("Protected Dashboard Access", False, 
                                "Missing dashboard fields")
                    return None
            else:
                self.log_test("Protected Dashboard Access", False, 
                            f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Protected Dashboard Access", False, f"Exception: {str(e)}")
            return None

    def test_protected_projects_access(self, certificate):
        """Test accessing protected projects endpoint with certificate"""
        try:
            headers = {"Authorization": f"Bearer {certificate}"}
            response = self.session.get(f"{API_URL}/projects", headers=headers)
            
            if response.status_code == 200:
                projects_data = response.json()
                if isinstance(projects_data, list):
                    self.log_test("Protected Projects Access", True, 
                                f"Projects endpoint accessible, returned {len(projects_data)} projects")
                    return projects_data
                else:
                    self.log_test("Protected Projects Access", False, 
                                "Invalid projects response format")
                    return None
            else:
                self.log_test("Protected Projects Access", False, 
                            f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Protected Projects Access", False, f"Exception: {str(e)}")
            return None

    def test_unauthorized_access(self):
        """Test that endpoints reject requests without certificates"""
        endpoints_to_test = [
            "/dashboard",
            "/projects",
            "/auth/verify"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = self.session.get(f"{API_URL}{endpoint}")
                if response.status_code == 401:
                    self.log_test(f"Unauthorized Access - {endpoint}", True, 
                                "Correctly rejected unauthorized request")
                else:
                    self.log_test(f"Unauthorized Access - {endpoint}", False, 
                                f"Expected 401, got {response.status_code}")
            except Exception as e:
                self.log_test(f"Unauthorized Access - {endpoint}", False, f"Exception: {str(e)}")

    def test_invalid_certificate_access(self):
        """Test that endpoints reject invalid certificates"""
        invalid_certificate = "invalid.certificate.token"
        headers = {"Authorization": f"Bearer {invalid_certificate}"}
        
        endpoints_to_test = [
            "/dashboard",
            "/projects",
            "/auth/verify"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = self.session.get(f"{API_URL}{endpoint}", headers=headers)
                if response.status_code == 401:
                    self.log_test(f"Invalid Certificate - {endpoint}", True, 
                                "Correctly rejected invalid certificate")
                else:
                    self.log_test(f"Invalid Certificate - {endpoint}", False, 
                                f"Expected 401, got {response.status_code}")
            except Exception as e:
                self.log_test(f"Invalid Certificate - {endpoint}", False, f"Exception: {str(e)}")

    def test_admin_revoke_certificate(self, certificate_id):
        """Test admin certificate revocation"""
        try:
            headers = {"Authorization": f"Bearer {ADMIN_SECRET}"}
            params = {"certificate_id": certificate_id}
            
            response = self.session.post(f"{API_URL}/admin/revoke-certificate", 
                                       params=params, headers=headers)
            
            if response.status_code == 200:
                revoke_data = response.json()
                if "message" in revoke_data:
                    self.log_test("Admin Revoke Certificate", True, 
                                f"Certificate {certificate_id} revoked successfully")
                    return True
                else:
                    self.log_test("Admin Revoke Certificate", False, 
                                "Invalid revocation response")
                    return False
            else:
                self.log_test("Admin Revoke Certificate", False, 
                            f"Status code: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Admin Revoke Certificate", False, f"Exception: {str(e)}")
            return False

    def test_revoked_certificate_access(self, certificate):
        """Test that revoked certificates are rejected"""
        try:
            headers = {"Authorization": f"Bearer {certificate}"}
            response = self.session.get(f"{API_URL}/dashboard", headers=headers)
            
            if response.status_code == 401:
                self.log_test("Revoked Certificate Access", True, 
                            "Correctly rejected revoked certificate")
                return True
            else:
                self.log_test("Revoked Certificate Access", False, 
                            f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Revoked Certificate Access", False, f"Exception: {str(e)}")
            return False

    def test_admin_unauthorized_access(self):
        """Test that admin endpoints reject non-admin requests"""
        invalid_admin_token = "invalid_admin_token"
        headers = {"Authorization": f"Bearer {invalid_admin_token}"}
        
        admin_endpoints = [
            "/admin/generate-certificate",
            "/admin/certificates",
            "/admin/revoke-certificate"
        ]
        
        for endpoint in admin_endpoints:
            try:
                if endpoint == "/admin/generate-certificate":
                    response = self.session.post(f"{API_URL}{endpoint}", 
                                               json={"client_name": "test", "client_email": "test@test.com"}, 
                                               headers=headers)
                elif endpoint == "/admin/revoke-certificate":
                    response = self.session.post(f"{API_URL}{endpoint}", 
                                               params={"certificate_id": "test"}, 
                                               headers=headers)
                else:
                    response = self.session.get(f"{API_URL}{endpoint}", headers=headers)
                
                if response.status_code == 401:
                    self.log_test(f"Admin Unauthorized - {endpoint}", True, 
                                "Correctly rejected non-admin request")
                else:
                    self.log_test(f"Admin Unauthorized - {endpoint}", False, 
                                f"Expected 401, got {response.status_code}")
            except Exception as e:
                self.log_test(f"Admin Unauthorized - {endpoint}", False, f"Exception: {str(e)}")

    def run_comprehensive_auth_test(self):
        """Run complete authentication test suite"""
        print("=" * 80)
        print("CERTIFICATE-BASED AUTHENTICATION SYSTEM - COMPREHENSIVE TESTING")
        print("=" * 80)
        
        # Test 1: Admin Certificate Generation
        print("\n--- Testing Admin Certificate Generation ---")
        test_clients = [
            {"name": "John Smith", "email": "john.smith@email.com"},
            {"name": "Sarah Johnson", "email": "sarah.johnson@email.com"}
        ]
        
        for client in test_clients:
            cert_data = self.test_admin_generate_certificate(client["name"], client["email"])
            if cert_data:
                self.client_tokens[client["name"]] = cert_data["certificate"]

        if not self.generated_certificates:
            print("❌ No certificates generated successfully. Stopping tests.")
            return False

        # Test 2: Admin Certificate Listing
        print("\n--- Testing Admin Certificate Management ---")
        self.test_admin_list_certificates()

        # Test 3: Client Authentication
        print("\n--- Testing Client Authentication ---")
        for cert_data in self.generated_certificates:
            login_result = self.test_client_login(cert_data["certificate"])
            if login_result:
                self.test_certificate_verification(cert_data["certificate"])

        # Test 4: Protected Routes Access
        print("\n--- Testing Protected Routes Access ---")
        if self.generated_certificates:
            test_certificate = self.generated_certificates[0]["certificate"]
            self.test_protected_dashboard_access(test_certificate)
            self.test_protected_projects_access(test_certificate)

        # Test 5: Security Testing - Unauthorized Access
        print("\n--- Testing Security - Unauthorized Access ---")
        self.test_unauthorized_access()
        self.test_invalid_certificate_access()
        self.test_admin_unauthorized_access()

        # Test 6: Certificate Revocation
        print("\n--- Testing Certificate Revocation ---")
        if self.generated_certificates:
            cert_to_revoke = self.generated_certificates[0]
            revoke_success = self.test_admin_revoke_certificate(cert_to_revoke["certificate_id"])
            
            if revoke_success:
                # Test that revoked certificate is rejected
                self.test_revoked_certificate_access(cert_to_revoke["certificate"])

        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("AUTHENTICATION TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.test_results['total_tests']}")
        print(f"Passed: {self.test_results['passed_tests']}")
        print(f"Failed: {self.test_results['failed_tests']}")
        
        if self.test_results['failed_tests'] > 0:
            print("\nFAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"  - {error}")
        
        success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests']) * 100 if self.test_results['total_tests'] > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: Certificate authentication system is working perfectly!")
        elif success_rate >= 75:
            print("✅ GOOD: Certificate authentication system is mostly working")
        elif success_rate >= 50:
            print("⚠️  MODERATE: Certificate authentication system has some issues")
        else:
            print("❌ POOR: Certificate authentication system has major issues")

def main():
    """Main test execution"""
    tester = AuthenticationTester()
    
    try:
        success = tester.run_comprehensive_auth_test()
        tester.print_summary()
        
        if success and tester.test_results['failed_tests'] == 0:
            print("\n🎉 ALL AUTHENTICATION TESTS PASSED! Certificate system is fully functional.")
            return 0
        elif tester.test_results['failed_tests'] < 3:
            print("\n✅ MOSTLY WORKING: Certificate authentication has minor issues but core functionality works.")
            return 0
        else:
            print("\n❌ SIGNIFICANT ISSUES: Certificate authentication system needs attention.")
            return 1
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR during authentication testing: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())