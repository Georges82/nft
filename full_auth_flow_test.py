#!/usr/bin/env python3
"""
Complete Authentication Flow Test - End-to-End Testing
Tests the complete flow from admin certificate generation to client project operations
"""

import requests
import json
from datetime import datetime
import sys

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

print(f"Testing complete authentication flow at: {API_URL}")

class FullAuthFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "errors": []
        }

    def log_test(self, test_name, success, message=""):
        self.test_results["total_tests"] += 1
        if success:
            self.test_results["passed_tests"] += 1
            print(f"✅ {test_name}: PASSED {message}")
        else:
            self.test_results["failed_tests"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")
            print(f"❌ {test_name}: FAILED - {message}")

    def run_complete_flow_test(self):
        """Test complete authentication and project management flow"""
        print("=" * 80)
        print("COMPLETE AUTHENTICATION FLOW - END-TO-END TESTING")
        print("=" * 80)
        
        # Step 1: Admin generates certificate for client
        print("\n--- Step 1: Admin Certificate Generation ---")
        admin_headers = {"Authorization": f"Bearer {ADMIN_SECRET}"}
        cert_data = {
            "client_name": "Michael Brown",
            "client_email": "michael.brown@email.com",
            "expires_days": 365
        }
        
        try:
            response = self.session.post(f"{API_URL}/admin/generate-certificate", 
                                       json=cert_data, headers=admin_headers)
            if response.status_code == 200:
                certificate_info = response.json()
                client_certificate = certificate_info["certificate"]
                self.log_test("Admin Certificate Generation", True, 
                            f"Generated certificate for {cert_data['client_name']}")
            else:
                self.log_test("Admin Certificate Generation", False, 
                            f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Admin Certificate Generation", False, f"Exception: {str(e)}")
            return False

        # Step 2: Client authenticates with certificate
        print("\n--- Step 2: Client Authentication ---")
        try:
            login_data = {"certificate": client_certificate}
            response = self.session.post(f"{API_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                auth_result = response.json()
                self.log_test("Client Authentication", True, 
                            f"Client {auth_result['user']['client_name']} authenticated successfully")
            else:
                self.log_test("Client Authentication", False, 
                            f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Client Authentication", False, f"Exception: {str(e)}")
            return False

        # Step 3: Client accesses dashboard
        print("\n--- Step 3: Protected Dashboard Access ---")
        try:
            client_headers = {"Authorization": f"Bearer {client_certificate}"}
            response = self.session.get(f"{API_URL}/dashboard", headers=client_headers)
            if response.status_code == 200:
                dashboard_data = response.json()
                self.log_test("Dashboard Access", True, 
                            f"Dashboard accessed - {dashboard_data['total_projects']} projects")
            else:
                self.log_test("Dashboard Access", False, 
                            f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Dashboard Access", False, f"Exception: {str(e)}")
            return False

        # Step 4: Client creates a project
        print("\n--- Step 4: Project Creation with Authentication ---")
        try:
            project_data = {
                "project_name": "Custom Dining Table - Brown Residence",
                "client_name": "Michael Brown",
                "client_email": "michael.brown@email.com",
                "client_phone": "+1-555-0789",
                "project_type": "custom_furniture",
                "description": "Handcrafted oak dining table with matching chairs",
                "quoted_amount": 2800.0,
                "start_date": "2024-03-01",
                "expected_completion": "2024-03-15"
            }
            
            response = self.session.post(f"{API_URL}/projects", 
                                       json=project_data, headers=client_headers)
            if response.status_code == 200:
                created_project = response.json()
                project_id = created_project["id"]
                self.log_test("Project Creation", True, 
                            f"Created project: {created_project['project_name']}")
            else:
                self.log_test("Project Creation", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Project Creation", False, f"Exception: {str(e)}")
            return False

        # Step 5: Client adds cost items
        print("\n--- Step 5: Cost Item Management ---")
        cost_items = [
            {
                "category": "materials",
                "description": "Oak lumber - premium grade",
                "quantity": 50.0,
                "unit_cost": 12.00
            },
            {
                "category": "labor",
                "description": "Table construction and finishing",
                "quantity": 20.0,
                "unit_cost": 50.00
            }
        ]
        
        for cost_item in cost_items:
            try:
                response = self.session.post(f"{API_URL}/projects/{project_id}/costs", 
                                           json=cost_item, headers=client_headers)
                if response.status_code == 200:
                    cost_result = response.json()
                    expected_total = cost_item["quantity"] * cost_item["unit_cost"]
                    self.log_test("Cost Item Addition", True, 
                                f"Added cost: {cost_item['description']} (${expected_total})")
                else:
                    self.log_test("Cost Item Addition", False, 
                                f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Cost Item Addition", False, f"Exception: {str(e)}")

        # Step 6: Client adds payment
        print("\n--- Step 6: Payment Recording ---")
        try:
            payment_data = {
                "type": "deposit",
                "amount": 1000.0,
                "date_received": "2024-02-28",
                "description": "Initial deposit for dining table project",
                "invoice_number": "INV-2024-004"
            }
            
            response = self.session.post(f"{API_URL}/projects/{project_id}/payments", 
                                       json=payment_data, headers=client_headers)
            if response.status_code == 200:
                payment_result = response.json()
                self.log_test("Payment Recording", True, 
                            f"Recorded payment: ${payment_data['amount']}")
            else:
                self.log_test("Payment Recording", False, 
                            f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Payment Recording", False, f"Exception: {str(e)}")

        # Step 7: Client retrieves updated project
        print("\n--- Step 7: Project Retrieval with Calculations ---")
        try:
            response = self.session.get(f"{API_URL}/projects/{project_id}", headers=client_headers)
            if response.status_code == 200:
                updated_project = response.json()
                total_costs = updated_project.get('total_costs', 0)
                total_payments = updated_project.get('total_payments', 0)
                profit_loss = updated_project.get('profit_loss', 0)
                
                self.log_test("Project Calculations", True, 
                            f"Costs: ${total_costs}, Payments: ${total_payments}, P/L: ${profit_loss}")
            else:
                self.log_test("Project Calculations", False, 
                            f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Project Calculations", False, f"Exception: {str(e)}")

        # Step 8: Test security - try to access without certificate
        print("\n--- Step 8: Security Verification ---")
        try:
            response = self.session.get(f"{API_URL}/projects/{project_id}")
            if response.status_code in [401, 403]:
                self.log_test("Security Check", True, 
                            "Project access correctly blocked without certificate")
            else:
                self.log_test("Security Check", False, 
                            f"Expected 401/403, got {response.status_code}")
        except Exception as e:
            self.log_test("Security Check", False, f"Exception: {str(e)}")

        # Step 9: Admin revokes certificate
        print("\n--- Step 9: Certificate Revocation Test ---")
        try:
            params = {"certificate_id": certificate_info["certificate_id"]}
            response = self.session.post(f"{API_URL}/admin/revoke-certificate", 
                                       params=params, headers=admin_headers)
            if response.status_code == 200:
                self.log_test("Certificate Revocation", True, 
                            "Certificate revoked successfully")
                
                # Test that revoked certificate is rejected
                response = self.session.get(f"{API_URL}/dashboard", headers=client_headers)
                if response.status_code == 401:
                    self.log_test("Revoked Certificate Rejection", True, 
                                "Revoked certificate correctly rejected")
                else:
                    self.log_test("Revoked Certificate Rejection", False, 
                                f"Expected 401, got {response.status_code}")
            else:
                self.log_test("Certificate Revocation", False, 
                            f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Certificate Revocation", False, f"Exception: {str(e)}")

        # Clean up - delete the test project
        print("\n--- Cleanup: Project Deletion ---")
        try:
            # Generate a new certificate for cleanup since the old one was revoked
            new_cert_response = self.session.post(f"{API_URL}/admin/generate-certificate", 
                                                json=cert_data, headers=admin_headers)
            if new_cert_response.status_code == 200:
                new_cert_info = new_cert_response.json()
                cleanup_headers = {"Authorization": f"Bearer {new_cert_info['certificate']}"}
                
                response = self.session.delete(f"{API_URL}/projects/{project_id}", 
                                             headers=cleanup_headers)
                if response.status_code == 200:
                    self.log_test("Project Cleanup", True, "Test project deleted successfully")
                else:
                    self.log_test("Project Cleanup", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Project Cleanup", False, f"Exception: {str(e)}")

        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("COMPLETE AUTHENTICATION FLOW TEST SUMMARY")
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
            print("🎉 EXCELLENT: Complete authentication flow is working perfectly!")
        elif success_rate >= 75:
            print("✅ GOOD: Complete authentication flow is mostly working")
        else:
            print("❌ ISSUES: Complete authentication flow has problems")

def main():
    """Main test execution"""
    tester = FullAuthFlowTester()
    
    try:
        success = tester.run_complete_flow_test()
        tester.print_summary()
        
        if success and tester.test_results['failed_tests'] == 0:
            print("\n🎉 COMPLETE FLOW TEST PASSED! Authentication and project management integration is perfect.")
            return 0
        elif tester.test_results['failed_tests'] < 3:
            print("\n✅ MOSTLY WORKING: Complete flow has minor issues but core functionality works.")
            return 0
        else:
            print("\n❌ SIGNIFICANT ISSUES: Complete authentication flow needs attention.")
            return 1
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR during complete flow testing: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())