import requests
import sys
import json
import base64
from datetime import datetime

class MediFlowAPITester:
    def __init__(self, base_url="https://pharmafast-13.preview.emergentagent.com"):
        self.base_url = base_url
        self.user_token = None
        self.pharmacist_token = None
        self.test_order_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    test_headers.pop('Content-Type', None)
                    response = requests.post(url, files=files, headers=test_headers)
                else:
                    response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                self.failed_tests.append({
                    'test': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'endpoint': endpoint
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                'test': name,
                'error': str(e),
                'endpoint': endpoint
            })
            return False, {}

    def test_user_registration(self):
        """Test user registration"""
        test_user_data = {
            "email": f"testuser_{datetime.now().strftime('%H%M%S')}@test.com",
            "password": "testpass123",
            "name": "Test User",
            "phone": "+1234567890",
            "address": "123 Test Street"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user_data
        )
        
        if success and 'token' in response:
            self.user_token = response['token']
            print(f"   User token obtained: {self.user_token[:20]}...")
            return True
        return False

    def test_user_login(self):
        """Test user login with demo credentials"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"email": "test@user.com", "password": "user123"}
        )
        
        if success and 'token' in response:
            self.user_token = response['token']
            print(f"   User token obtained: {self.user_token[:20]}...")
            return True
        return False

    def test_pharmacist_login(self):
        """Test pharmacist login"""
        success, response = self.run_test(
            "Pharmacist Login",
            "POST",
            "auth/pharmacist/login",
            200,
            data={"email": "dr.smith@mediflow.com", "password": "pharm123"}
        )
        
        if success and 'token' in response:
            self.pharmacist_token = response['token']
            print(f"   Pharmacist token obtained: {self.pharmacist_token[:20]}...")
            return True
        return False

    def test_get_medicines(self):
        """Test getting medicines list"""
        success, response = self.run_test(
            "Get Medicines",
            "GET",
            "medicines",
            200
        )
        
        if success and isinstance(response, list) and len(response) > 0:
            print(f"   Found {len(response)} medicines")
            return True
        return False

    def test_get_categories(self):
        """Test getting medicine categories"""
        success, response = self.run_test(
            "Get Categories",
            "GET",
            "categories",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} categories")
            return True
        return False

    def test_create_order(self):
        """Test creating an order"""
        if not self.user_token:
            print("❌ Cannot test order creation - no user token")
            return False

        headers = {'Authorization': f'Bearer {self.user_token}'}
        
        success, response = self.run_test(
            "Create Order",
            "POST",
            "orders",
            200,
            data={
                "order_type": "PRESCRIPTION",
                "items": []
            },
            headers=headers
        )
        
        if success and 'id' in response:
            self.test_order_id = response['id']
            print(f"   Order created with ID: {self.test_order_id}")
            return True
        return False

    def test_upload_prescription(self):
        """Test prescription upload"""
        if not self.user_token or not self.test_order_id:
            print("❌ Cannot test prescription upload - missing token or order ID")
            return False

        # Create a simple test image (1x1 pixel PNG)
        test_image_data = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==')
        
        headers = {'Authorization': f'Bearer {self.user_token}'}
        files = {'file': ('test_prescription.png', test_image_data, 'image/png')}
        
        success, response = self.run_test(
            "Upload Prescription",
            "POST",
            f"orders/{self.test_order_id}/prescription",
            200,
            headers=headers,
            files=files
        )
        
        return success

    def test_pharmacist_queue(self):
        """Test pharmacist queue access"""
        if not self.pharmacist_token:
            print("❌ Cannot test pharmacist queue - no pharmacist token")
            return False

        headers = {'Authorization': f'Bearer {self.pharmacist_token}'}
        
        success, response = self.run_test(
            "Get Pharmacist Queue",
            "GET",
            "pharmacist/queue",
            200,
            headers=headers
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} orders in queue")
            return True
        return False

    def test_accept_call(self):
        """Test accepting a call"""
        if not self.pharmacist_token or not self.test_order_id:
            print("❌ Cannot test accept call - missing token or order ID")
            return False

        headers = {'Authorization': f'Bearer {self.pharmacist_token}'}
        
        success, response = self.run_test(
            "Accept Call",
            "POST",
            f"pharmacist/accept-call/{self.test_order_id}",
            200,
            headers=headers
        )
        
        return success

    def test_get_my_orders(self):
        """Test getting user's orders"""
        if not self.user_token:
            print("❌ Cannot test get orders - no user token")
            return False

        headers = {'Authorization': f'Bearer {self.user_token}'}
        
        success, response = self.run_test(
            "Get My Orders",
            "GET",
            "orders/my-orders",
            200,
            headers=headers
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} orders")
            return True
        return False

    def test_payment_process(self):
        """Test payment processing"""
        if not self.user_token or not self.test_order_id:
            print("❌ Cannot test payment - missing token or order ID")
            return False

        headers = {'Authorization': f'Bearer {self.user_token}'}
        
        success, response = self.run_test(
            "Process Payment",
            "POST",
            "payment/process",
            200,
            data={
                "order_id": self.test_order_id,
                "payment_method": "UPI"
            },
            headers=headers
        )
        
        return success

    def test_invalid_auth(self):
        """Test invalid authentication"""
        headers = {'Authorization': 'Bearer invalid_token'}
        
        success, response = self.run_test(
            "Invalid Auth Test",
            "GET",
            "auth/me",
            401,
            headers=headers
        )
        
        return success

def main():
    print("🚀 Starting MediFlow API Testing...")
    print("=" * 50)
    
    tester = MediFlowAPITester()
    
    # Test sequence
    test_sequence = [
        ("User Registration", tester.test_user_registration),
        ("User Login", tester.test_user_login),
        ("Pharmacist Login", tester.test_pharmacist_login),
        ("Get Medicines", tester.test_get_medicines),
        ("Get Categories", tester.test_get_categories),
        ("Create Order", tester.test_create_order),
        ("Upload Prescription", tester.test_upload_prescription),
        ("Pharmacist Queue", tester.test_pharmacist_queue),
        ("Accept Call", tester.test_accept_call),
        ("Get My Orders", tester.test_get_my_orders),
        ("Payment Process", tester.test_payment_process),
        ("Invalid Auth", tester.test_invalid_auth),
    ]
    
    print(f"Running {len(test_sequence)} test scenarios...\n")
    
    for test_name, test_func in test_sequence:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            tester.failed_tests.append({
                'test': test_name,
                'error': str(e)
            })
    
    # Print results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.failed_tests:
        print("\n❌ FAILED TESTS:")
        for failure in tester.failed_tests:
            print(f"  - {failure['test']}: {failure.get('error', f\"Expected {failure.get('expected')}, got {failure.get('actual')}\"")}")
    
    print("\n✅ Backend API testing completed!")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())