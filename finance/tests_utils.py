"""
Unit tests for finance utils
"""
from django.test import TestCase
from django.http import HttpResponse
import json
from finance.utils import add_htmx_trigger, add_toast_trigger


class FinanceUtilsTestCase(TestCase):
    """Test utility functions"""
    
    def test_add_htmx_trigger_simple(self):
        """Test adding simple HTMX trigger"""
        response = HttpResponse()
        result = add_htmx_trigger(response, 'test-event')
        
        self.assertEqual(result, response)
        self.assertIn('HX-Trigger', response)
        
        trigger_data = json.loads(response['HX-Trigger'])
        self.assertIn('test-event', trigger_data)
    
    def test_add_htmx_trigger_with_data(self):
        """Test adding HTMX trigger with data"""
        response = HttpResponse()
        data = {'key': 'value', 'number': 123}
        result = add_htmx_trigger(response, 'test-event', data)
        
        trigger_data = json.loads(response['HX-Trigger'])
        self.assertEqual(trigger_data['test-event'], data)
    
    def test_add_htmx_trigger_multiple(self):
        """Test adding multiple HTMX triggers"""
        response = HttpResponse()
        add_htmx_trigger(response, 'event1', {'data1': 'value1'})
        add_htmx_trigger(response, 'event2', {'data2': 'value2'})
        
        trigger_data = json.loads(response['HX-Trigger'])
        self.assertIn('event1', trigger_data)
        self.assertIn('event2', trigger_data)
        self.assertEqual(trigger_data['event1']['data1'], 'value1')
        self.assertEqual(trigger_data['event2']['data2'], 'value2')
    
    def test_add_htmx_trigger_existing_invalid_json(self):
        """Test adding trigger when existing header has invalid JSON"""
        response = HttpResponse()
        response['HX-Trigger'] = 'invalid-json'
        result = add_htmx_trigger(response, 'test-event')
        
        # Should still work, ignoring invalid existing trigger
        trigger_data = json.loads(response['HX-Trigger'])
        self.assertIn('test-event', trigger_data)
    
    def test_add_toast_trigger_success(self):
        """Test adding toast trigger for success"""
        response = HttpResponse()
        result = add_toast_trigger(response, 'Success message', 'success')
        
        trigger_data = json.loads(response['HX-Trigger'])
        self.assertIn('show-toast', trigger_data)
        toast_data = trigger_data['show-toast']
        self.assertEqual(toast_data['message'], 'Success message')
        self.assertEqual(toast_data['type'], 'success')
    
    def test_add_toast_trigger_error(self):
        """Test adding toast trigger for error"""
        response = HttpResponse()
        result = add_toast_trigger(response, 'Error message', 'error')
        
        trigger_data = json.loads(response['HX-Trigger'])
        toast_data = trigger_data['show-toast']
        self.assertEqual(toast_data['type'], 'error')
    
    def test_add_toast_trigger_info(self):
        """Test adding toast trigger for info"""
        response = HttpResponse()
        result = add_toast_trigger(response, 'Info message', 'info')
        
        trigger_data = json.loads(response['HX-Trigger'])
        toast_data = trigger_data['show-toast']
        self.assertEqual(toast_data['type'], 'info')
    
    def test_add_toast_trigger_default(self):
        """Test adding toast trigger with default type"""
        response = HttpResponse()
        result = add_toast_trigger(response, 'Default message')
        
        trigger_data = json.loads(response['HX-Trigger'])
        toast_data = trigger_data['show-toast']
        self.assertEqual(toast_data['type'], 'success')

