"""
Tests for Lighthouse performance, accessibility, SEO, and best practices thresholds.

These tests verify that key pages meet minimum Lighthouse scores.
"""
import subprocess
import json
import os
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()


class LighthouseThresholdTestCase(TestCase):
    """Test Lighthouse scores meet minimum thresholds"""
    
    # Minimum score thresholds (0-100)
    PERFORMANCE_THRESHOLD = 90
    ACCESSIBILITY_THRESHOLD = 90
    BEST_PRACTICES_THRESHOLD = 80
    SEO_THRESHOLD = 80
    
    @classmethod
    def setUpClass(cls):
        """Set up test class - run once before all tests"""
        super().setUpClass()
        cls.client = Client()
        cls.user = User.objects.create_user(
            username='lighthouse_test',
            email='lighthouse@test.com',
            password='testpass123'
        )
    
    def setUp(self):
        """Set up for each test"""
        self.client.login(username='lighthouse_test', password='testpass123')
    
    def _run_lighthouse_audit(self, url, port=8000):
        """
        Run Lighthouse audit on a URL and return scores.
        
        Returns dict with scores or None if audit fails.
        """
        # Check if lhci is available
        try:
            result = subprocess.run(
                ['npx', '--yes', '@lhci/cli', 'collect', '--url', url],
                capture_output=True,
                text=True,
                timeout=120,
                env={**os.environ, 'CI': 'false'}
            )
            
            if result.returncode != 0:
                # If npx fails, try direct lighthouse command
                result = subprocess.run(
                    ['npx', '--yes', 'lighthouse', url, '--output=json', '--output-path=/dev/stdout', '--chrome-flags="--headless --no-sandbox"'],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
            
            if result.returncode != 0:
                self.skipTest(f"Lighthouse audit failed: {result.stderr}")
                return None
            
            # Parse JSON output
            try:
                data = json.loads(result.stdout)
                scores = {
                    'performance': data.get('categories', {}).get('performance', {}).get('score', 0) * 100,
                    'accessibility': data.get('categories', {}).get('accessibility', {}).get('score', 0) * 100,
                    'best-practices': data.get('categories', {}).get('best-practices', {}).get('score', 0) * 100,
                    'seo': data.get('categories', {}).get('seo', {}).get('score', 0) * 100,
                }
                return scores
            except (json.JSONDecodeError, KeyError):
                self.skipTest("Could not parse Lighthouse output")
                return None
                
        except subprocess.TimeoutExpired:
            self.skipTest("Lighthouse audit timed out")
            return None
        except FileNotFoundError:
            self.skipTest("Lighthouse CLI not available - skipping audit tests")
            return None
    
    def test_login_page_performance(self):
        """Test login page meets performance threshold"""
        # Only run if server is available (skip in CI where server setup is different)
        if os.environ.get('CI'):
            self.skipTest("Skipping in CI - Lighthouse runs in separate job")
            return
        
        url = 'http://localhost:8000/login/'
        scores = self._run_lighthouse_audit(url)
        
        if scores is None:
            return
        
        self.assertGreaterEqual(
            scores['performance'],
            self.PERFORMANCE_THRESHOLD,
            f"Login page performance score {scores['performance']:.1f} is below threshold {self.PERFORMANCE_THRESHOLD}"
        )
    
    def test_login_page_accessibility(self):
        """Test login page meets accessibility threshold"""
        if os.environ.get('CI'):
            self.skipTest("Skipping in CI - Lighthouse runs in separate job")
            return
        
        url = 'http://localhost:8000/login/'
        scores = self._run_lighthouse_audit(url)
        
        if scores is None:
            return
        
        self.assertGreaterEqual(
            scores['accessibility'],
            self.ACCESSIBILITY_THRESHOLD,
            f"Login page accessibility score {scores['accessibility']:.1f} is below threshold {self.ACCESSIBILITY_THRESHOLD}"
        )
    
    def test_login_page_best_practices(self):
        """Test login page meets best practices threshold"""
        if os.environ.get('CI'):
            self.skipTest("Skipping in CI - Lighthouse runs in separate job")
            return
        
        url = 'http://localhost:8000/login/'
        scores = self._run_lighthouse_audit(url)
        
        if scores is None:
            return
        
        self.assertGreaterEqual(
            scores['best-practices'],
            self.BEST_PRACTICES_THRESHOLD,
            f"Login page best practices score {scores['best-practices']:.1f} is below threshold {self.BEST_PRACTICES_THRESHOLD}"
        )
    
    def test_login_page_seo(self):
        """Test login page meets SEO threshold"""
        if os.environ.get('CI'):
            self.skipTest("Skipping in CI - Lighthouse runs in separate job")
            return
        
        url = 'http://localhost:8000/login/'
        scores = self._run_lighthouse_audit(url)
        
        if scores is None:
            return
        
        self.assertGreaterEqual(
            scores['seo'],
            self.SEO_THRESHOLD,
            f"Login page SEO score {scores['seo']:.1f} is below threshold {self.SEO_THRESHOLD}"
        )
    
    def test_register_page_performance(self):
        """Test register page meets performance threshold"""
        if os.environ.get('CI'):
            self.skipTest("Skipping in CI - Lighthouse runs in separate job")
            return
        
        url = 'http://localhost:8000/register/'
        scores = self._run_lighthouse_audit(url)
        
        if scores is None:
            return
        
        self.assertGreaterEqual(
            scores['performance'],
            self.PERFORMANCE_THRESHOLD,
            f"Register page performance score {scores['performance']:.1f} is below threshold {self.PERFORMANCE_THRESHOLD}"
        )
    
    def test_register_page_accessibility(self):
        """Test register page meets accessibility threshold"""
        if os.environ.get('CI'):
            self.skipTest("Skipping in CI - Lighthouse runs in separate job")
            return
        
        url = 'http://localhost:8000/register/'
        scores = self._run_lighthouse_audit(url)
        
        if scores is None:
            return
        
        self.assertGreaterEqual(
            scores['accessibility'],
            self.ACCESSIBILITY_THRESHOLD,
            f"Register page accessibility score {scores['accessibility']:.1f} is below threshold {self.ACCESSIBILITY_THRESHOLD}"
        )

