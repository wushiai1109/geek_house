import unittest

from geek_house.utils.image_storage import storage
from werkzeug.security import generate_password_hash, check_password_hash


class MyTestCase(unittest.TestCase):
    def test_storage(self):
        with open("1.png", "rb") as f:
            file_data = f.read()
        self.assertEqual(storage(file_data), "FopgBrRfZGvRsrljDyrn2UfonPEq")
        self.assertTrue(storage(file_data))
        print(storage(file_data))

    def test_dict(self):
        d = dict(a=1, b='test')
        self.assertEqual(d["a"], 1)
        self.assertEqual(d.get("b"), 'test')
        self.assertTrue(isinstance(d, dict))

    def test_generate_password_hash(self):
        """对密码进行加密"""
        mobile = "18716848159"
        hash_password_test = "pbkdf2:sha256:150000$u2Y14Sl0$cae62b06caf78865f4c827ce60ee542bccd8d516cf2928a2f2e47338b71c87a1"
        hash_password = generate_password_hash(mobile)
        self.assertTrue(check_password_hash(hash_password_test, mobile))
        self.assertTrue(check_password_hash(hash_password, mobile))
        self.assertTrue(hash_password_test != hash_password)

    def test_path(self):
        import os
        path = os.path.dirname(__file__)
        print(os.path.abspath(os.path.join(path, "..")))
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
