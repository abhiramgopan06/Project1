from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from orders.models import Coupon

class CouponModelTests(TestCase):
    def test_coupon_can_be_saved(self):
        coupon = Coupon.objects.create(code='WELCOME10', discount_percent=10)
        self.assertEqual(coupon.code, 'WELCOME10')
        self.assertEqual(coupon.discount_percent, 10)

    def test_coupon_expiry_can_be_set(self):
        expires = timezone.now() + timedelta(days=1)
        coupon = Coupon.objects.create(code='FUTURE', expires_at=expires)
        self.assertGreater(coupon.expires_at, timezone.now())
