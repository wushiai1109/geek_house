import unittest

from geek_house.utils.image_storage import storage


class MyTestCase(unittest.TestCase):
    def test_something(self):
        with open("1.png", "rb") as f:
            file_data = f.read()
        self.assertEqual(storage(file_data), "FopgBrRfZGvRsrljDyrn2UfonPEq")
        self.assertTrue(storage(file_data))
        print(storage(file_data))


if __name__ == '__main__':
    unittest.main()
