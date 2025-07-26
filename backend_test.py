#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Joinery Project Management System
Tests all CRUD operations, cost management, payment tracking, and dashboard statistics
"""

import requests
import json
from datetime import datetime, date
import uuid
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
print(f"Testing backend API at: {API_URL}")

# Test data for realistic joinery projects
TEST_PROJECTS = [
    {
        "project_name": "Modern Kitchen Cabinets - Smith Residence",
        "client_name": "John Smith",
        "client_email": "john.smith@email.com",
        "client_phone": "+1-555-0123",
        "project_type": "kitchen_cabinets",
        "description": "Complete kitchen renovation with custom oak cabinets, soft-close hinges, and granite countertop support",
        "quoted_amount": 8500.0,
        "start_date": "2024-01-15",
        "expected_completion": "2024-02-28"
    },
    {
        "project_name": "Built-in Entertainment Center",
        "client_name": "Sarah Johnson",
        "client_email": "sarah.j@email.com", 
        "client_phone": "+1-555-0456",
        "project_type": "built_ins",
        "description": "Custom built-in entertainment center with LED lighting and cable management",
        "quoted_amount": 3200.0,
        "start_date": "2024-02-01",
        "expected_completion": "2024-02-15"
    }
]

TEST_COST_ITEMS = [
    {
        "category": "materials",
        "description": "Oak hardwood boards - 200 board feet",
        "quantity": 200.0,
        "unit_cost": 8.50
    },
    {
        "category": "materials", 
        "description": "Cabinet hardware - hinges and handles",
        "quantity": 24.0,
        "unit_cost": 12.75
    },
    {
        "category": "labor",
        "description": "Cabinet construction and installation",
        "quantity": 40.0,
        "unit_cost": 45.00
    },
    {
        "category": "equipment",
        "description": "Router bit set rental",
        "quantity": 1.0,
        "unit_cost": 85.00
    },
    {
        "category": "overhead",
        "description": "Shop utilities and insurance allocation",
        "quantity": 1.0,
        "unit_cost": 150.00
    }
]

TEST_PAYMENTS = [
    {
        "type": "deposit",
        "amount": 2500.0,
        "date_received": "2024-01-10",
        "description": "Initial deposit - 30% of quoted amount",
        "invoice_number": "INV-2024-001"
    },
    {
        "type": "progress_payment",
        "amount": 3000.0,
        "date_received": "2024-01-25",
        "description": "Progress payment - materials purchased",
        "invoice_number": "INV-2024-002"
    },
    {
        "type": "final_payment",
        "amount": 3000.0,
        "date_received": "2024-02-28",
        "description": "Final payment upon completion",
        "invoice_number": "INV-2024-003"
    }
]

class JoineryAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.created_projects = []
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

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = self.session.get(f"{API_URL}/")
            if response.status_code == 200:
                data = response.json()
                if "Joinery Project Management API" in data.get("message", ""):
                    self.log_test("API Root", True, "API is accessible")
                    return True
                else:
                    self.log_test("API Root", False, f"Unexpected message: {data}")
                    return False
            else:
                self.log_test("API Root", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Root", False, f"Exception: {str(e)}")
            return False

    def test_create_project(self, project_data):
        """Test project creation"""
        try:
            response = self.session.post(f"{API_URL}/projects", json=project_data)
            if response.status_code == 200:
                project = response.json()
                if project.get("id") and project.get("project_name") == project_data["project_name"]:
                    self.created_projects.append(project)
                    self.log_test("Create Project", True, f"Created project: {project['project_name']}")
                    return project
                else:
                    self.log_test("Create Project", False, f"Invalid response data: {project}")
                    return None
            else:
                self.log_test("Create Project", False, f"Status code: {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            self.log_test("Create Project", False, f"Exception: {str(e)}")
            return None

    def test_get_projects(self):
        """Test getting all projects"""
        try:
            response = self.session.get(f"{API_URL}/projects")
            if response.status_code == 200:
                projects = response.json()
                if isinstance(projects, list):
                    self.log_test("Get Projects", True, f"Retrieved {len(projects)} projects")
                    return projects
                else:
                    self.log_test("Get Projects", False, f"Expected list, got: {type(projects)}")
                    return None
            else:
                self.log_test("Get Projects", False, f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Get Projects", False, f"Exception: {str(e)}")
            return None

    def test_get_project_by_id(self, project_id):
        """Test getting specific project"""
        try:
            response = self.session.get(f"{API_URL}/projects/{project_id}")
            if response.status_code == 200:
                project = response.json()
                if project.get("id") == project_id:
                    self.log_test("Get Project by ID", True, f"Retrieved project: {project.get('project_name')}")
                    return project
                else:
                    self.log_test("Get Project by ID", False, f"ID mismatch: expected {project_id}, got {project.get('id')}")
                    return None
            else:
                self.log_test("Get Project by ID", False, f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Get Project by ID", False, f"Exception: {str(e)}")
            return None

    def test_update_project(self, project_id, update_data):
        """Test project update"""
        try:
            response = self.session.put(f"{API_URL}/projects/{project_id}", json=update_data)
            if response.status_code == 200:
                project = response.json()
                updated = False
                for key, value in update_data.items():
                    if project.get(key) == value:
                        updated = True
                        break
                if updated:
                    self.log_test("Update Project", True, f"Updated project successfully")
                    return project
                else:
                    self.log_test("Update Project", False, f"Update not reflected in response")
                    return None
            else:
                self.log_test("Update Project", False, f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Update Project", False, f"Exception: {str(e)}")
            return None

    def test_add_cost_item(self, project_id, cost_data):
        """Test adding cost item to project"""
        try:
            response = self.session.post(f"{API_URL}/projects/{project_id}/costs", json=cost_data)
            if response.status_code == 200:
                cost_item = response.json()
                expected_total = cost_data["quantity"] * cost_data["unit_cost"]
                if cost_item.get("total_cost") == expected_total:
                    self.log_test("Add Cost Item", True, f"Added cost: {cost_data['description']} (${expected_total})")
                    return cost_item
                else:
                    self.log_test("Add Cost Item", False, f"Total cost calculation error: expected {expected_total}, got {cost_item.get('total_cost')}")
                    return None
            else:
                self.log_test("Add Cost Item", False, f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Add Cost Item", False, f"Exception: {str(e)}")
            return None

    def test_add_payment(self, project_id, payment_data):
        """Test adding payment to project"""
        try:
            response = self.session.post(f"{API_URL}/projects/{project_id}/payments", json=payment_data)
            if response.status_code == 200:
                payment = response.json()
                if payment.get("amount") == payment_data["amount"]:
                    self.log_test("Add Payment", True, f"Added payment: ${payment_data['amount']} ({payment_data['type']})")
                    return payment
                else:
                    self.log_test("Add Payment", False, f"Payment amount mismatch")
                    return None
            else:
                self.log_test("Add Payment", False, f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Add Payment", False, f"Exception: {str(e)}")
            return None

    def test_project_calculations(self, project_id):
        """Test project financial calculations"""
        try:
            response = self.session.get(f"{API_URL}/projects/{project_id}")
            if response.status_code == 200:
                project = response.json()
                
                # Verify calculated fields exist
                required_fields = ['total_costs', 'total_payments', 'profit_loss', 'outstanding_amount']
                missing_fields = [field for field in required_fields if field not in project]
                
                if not missing_fields:
                    # Verify calculations
                    costs = project.get('costs', [])
                    payments = project.get('payments', [])
                    
                    expected_total_costs = sum(cost.get('total_cost', 0) for cost in costs)
                    expected_total_payments = sum(payment.get('amount', 0) for payment in payments)
                    expected_profit_loss = expected_total_payments - expected_total_costs
                    expected_outstanding = project.get('quoted_amount', 0) - expected_total_payments
                    
                    calculations_correct = (
                        abs(project['total_costs'] - expected_total_costs) < 0.01 and
                        abs(project['total_payments'] - expected_total_payments) < 0.01 and
                        abs(project['profit_loss'] - expected_profit_loss) < 0.01 and
                        abs(project['outstanding_amount'] - expected_outstanding) < 0.01
                    )
                    
                    if calculations_correct:
                        self.log_test("Project Calculations", True, 
                                    f"Costs: ${project['total_costs']}, Payments: ${project['total_payments']}, Profit: ${project['profit_loss']}")
                        return True
                    else:
                        self.log_test("Project Calculations", False, 
                                    f"Calculation mismatch - Expected costs: {expected_total_costs}, got: {project['total_costs']}")
                        return False
                else:
                    self.log_test("Project Calculations", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Project Calculations", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Project Calculations", False, f"Exception: {str(e)}")
            return False

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        try:
            response = self.session.get(f"{API_URL}/dashboard")
            if response.status_code == 200:
                stats = response.json()
                required_fields = ['total_projects', 'active_projects', 'completed_projects', 
                                 'total_revenue', 'total_costs', 'total_profit', 'pending_payments']
                missing_fields = [field for field in required_fields if field not in stats]
                
                if not missing_fields:
                    # Verify stats make sense
                    if (stats['total_projects'] >= 0 and 
                        stats['active_projects'] >= 0 and
                        stats['completed_projects'] >= 0 and
                        stats['total_projects'] >= stats['active_projects'] + stats['completed_projects']):
                        self.log_test("Dashboard Stats", True, 
                                    f"Projects: {stats['total_projects']}, Revenue: ${stats['total_revenue']}, Profit: ${stats['total_profit']}")
                        return stats
                    else:
                        self.log_test("Dashboard Stats", False, "Invalid statistics values")
                        return None
                else:
                    self.log_test("Dashboard Stats", False, f"Missing fields: {missing_fields}")
                    return None
            else:
                self.log_test("Dashboard Stats", False, f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Dashboard Stats", False, f"Exception: {str(e)}")
            return None

    def test_delete_cost_item(self, project_id, cost_id):
        """Test deleting cost item"""
        try:
            response = self.session.delete(f"{API_URL}/projects/{project_id}/costs/{cost_id}")
            if response.status_code == 200:
                self.log_test("Delete Cost Item", True, f"Deleted cost item: {cost_id}")
                return True
            else:
                self.log_test("Delete Cost Item", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Delete Cost Item", False, f"Exception: {str(e)}")
            return False

    def test_delete_payment(self, project_id, payment_id):
        """Test deleting payment"""
        try:
            response = self.session.delete(f"{API_URL}/projects/{project_id}/payments/{payment_id}")
            if response.status_code == 200:
                self.log_test("Delete Payment", True, f"Deleted payment: {payment_id}")
                return True
            else:
                self.log_test("Delete Payment", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Delete Payment", False, f"Exception: {str(e)}")
            return False

    def test_delete_project(self, project_id):
        """Test project deletion"""
        try:
            response = self.session.delete(f"{API_URL}/projects/{project_id}")
            if response.status_code == 200:
                self.log_test("Delete Project", True, f"Deleted project: {project_id}")
                return True
            else:
                self.log_test("Delete Project", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Delete Project", False, f"Exception: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Run complete test suite"""
        print("=" * 80)
        print("JOINERY PROJECT MANAGEMENT API - COMPREHENSIVE TESTING")
        print("=" * 80)
        
        # Test 1: API Root
        if not self.test_api_root():
            print("❌ API is not accessible. Stopping tests.")
            return False

        # Test 2: Create Projects
        print("\n--- Testing Project Creation ---")
        for project_data in TEST_PROJECTS:
            project = self.test_create_project(project_data)
            if not project:
                continue

        if not self.created_projects:
            print("❌ No projects created successfully. Stopping tests.")
            return False

        # Test 3: Get Projects
        print("\n--- Testing Project Retrieval ---")
        projects = self.test_get_projects()
        
        # Test 4: Get Specific Project
        if self.created_projects:
            project_id = self.created_projects[0]["id"]
            self.test_get_project_by_id(project_id)

        # Test 5: Update Project
        print("\n--- Testing Project Updates ---")
        if self.created_projects:
            project_id = self.created_projects[0]["id"]
            update_data = {"status": "confirmed", "quoted_amount": 9000.0}
            self.test_update_project(project_id, update_data)

        # Test 6: Add Cost Items
        print("\n--- Testing Cost Item Management ---")
        if self.created_projects:
            project_id = self.created_projects[0]["id"]
            added_costs = []
            for cost_data in TEST_COST_ITEMS:
                cost_item = self.test_add_cost_item(project_id, cost_data)
                if cost_item:
                    added_costs.append(cost_item)

        # Test 7: Add Payments
        print("\n--- Testing Payment Recording ---")
        if self.created_projects:
            project_id = self.created_projects[0]["id"]
            added_payments = []
            for payment_data in TEST_PAYMENTS:
                payment = self.test_add_payment(project_id, payment_data)
                if payment:
                    added_payments.append(payment)

        # Test 8: Verify Calculations
        print("\n--- Testing Financial Calculations ---")
        if self.created_projects:
            project_id = self.created_projects[0]["id"]
            self.test_project_calculations(project_id)

        # Test 9: Dashboard Statistics
        print("\n--- Testing Dashboard Statistics ---")
        self.test_dashboard_stats()

        # Test 10: Delete Operations
        print("\n--- Testing Delete Operations ---")
        if self.created_projects:
            project_id = self.created_projects[0]["id"]
            
            # Get project to find cost and payment IDs
            project = self.test_get_project_by_id(project_id)
            if project:
                # Delete a cost item if exists
                if project.get('costs'):
                    cost_id = project['costs'][0]['id']
                    self.test_delete_cost_item(project_id, cost_id)
                
                # Delete a payment if exists
                if project.get('payments'):
                    payment_id = project['payments'][0]['id']
                    self.test_delete_payment(project_id, payment_id)

        # Test 11: Clean up - Delete Projects
        print("\n--- Cleaning Up Test Data ---")
        for project in self.created_projects:
            self.test_delete_project(project["id"])

        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
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
            print("🎉 EXCELLENT: Backend API is working very well!")
        elif success_rate >= 75:
            print("✅ GOOD: Backend API is mostly working with minor issues")
        elif success_rate >= 50:
            print("⚠️  MODERATE: Backend API has some significant issues")
        else:
            print("❌ POOR: Backend API has major issues that need attention")

def main():
    """Main test execution"""
    tester = JoineryAPITester()
    
    try:
        success = tester.run_comprehensive_test()
        tester.print_summary()
        
        if success and tester.test_results['failed_tests'] == 0:
            print("\n🎉 ALL TESTS PASSED! Backend API is fully functional.")
            return 0
        elif tester.test_results['failed_tests'] < 3:
            print("\n✅ MOSTLY WORKING: Backend API has minor issues but core functionality works.")
            return 0
        else:
            print("\n❌ SIGNIFICANT ISSUES: Backend API needs attention.")
            return 1
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR during testing: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())