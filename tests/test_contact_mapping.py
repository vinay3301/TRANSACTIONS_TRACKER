import unittest

from TranscationsUpdater import (
    extract_amount,
    extract_counterparty,
    extract_purpose,
    map_contact_name,
)

THRUPTHI_SMS = """Sent Rs.80.00
From HDFC Bank A/C *4299
To THRUPTHI FOOD COURT
On 27/11/26
Ref 654605983316
Not You?
Call 18002586161/SMS BLOCK UPI to 7308080808"""


class ContactMappingRegressionTests(unittest.TestCase):
    def test_multiline_thrupthi_sms_maps_to_existing_food_court_name(self):
        self.assertEqual(extract_amount(THRUPTHI_SMS), 80.00)
        self.assertEqual(extract_purpose(THRUPTHI_SMS, bank="HDFC"), "TRUPTI FOOD COURT")

    def test_single_line_to_field_is_extracted(self):
        body = "Sent Rs.80.00 From HDFC Bank A/C *4299 To THRUPTHI FOOD COURT On 27/11/26 Ref 654605983316"
        self.assertEqual(extract_counterparty(body), "THRUPTHI FOOD COURT")
        self.assertEqual(extract_purpose(body, bank="HDFC"), "TRUPTI FOOD COURT")

    def test_to_info_field_variants_are_supported(self):
        self.assertEqual(extract_counterparty("Sent Rs.20 To|Info: LOCAL SHOP On 27/11/26 Ref 123"), "LOCAL SHOP")
        self.assertEqual(extract_counterparty("Sent Rs.20 Info: MEDICAL STORE Ref 123"), "MEDICAL STORE")

    def test_vpa_fallback_is_used_for_debit(self):
        body = "UPI payment debited Rs.100 VPA *0866@ybl Ref 123456"
        self.assertEqual(extract_purpose(body, bank="HDFC"), "MOM or MAA")

    def test_upi_user_credit_maps_known_contact(self):
        body = "UPI User *0866@ybl credited with Rs.500 Ref No 123456"
        self.assertEqual(extract_purpose(body, bank="BOB"), "MOM or MAA")

    def test_existing_mom_alias_variants_remain_mapped(self):
        self.assertEqual(map_contact_name("*0866@ybl"), "MOM or MAA")
        self.assertEqual(map_contact_name("0866@axl"), "MOM or MAA")
        self.assertEqual(map_contact_name("7981540866"), "MOM or MAA")

    def test_unknown_counterparty_is_preserved(self):
        self.assertEqual(extract_purpose("Sent Rs.25 To UNKNOWN MERCHANT On 27/11/26 Ref 123"), "UNKNOWN MERCHANT")


if __name__ == "__main__":
    unittest.main()
