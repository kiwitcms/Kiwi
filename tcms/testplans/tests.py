# -*- coding: utf-8 -*-
import unittest

from django.test.client import Client


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.c = Client()
        self.plan_id = 2256
        self.status_codes = [301, 302]

    def test_plans(self):
        response = self.c.get('/plans/')
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError:
            self.assertEquals(response.status_code, 302)

    def test_plan_new(self):
        response = self.c.get('/plan/new/')
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError:
            self.assertEquals(response.status_code, 302)

    def test_plan_clone(self):
        response = self.c.get('/plans/clone/', {'plan_id': self.plan_id})
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError:
            assert response.status_code in self.status_codes

    def test_plan_details(self):
        location = '/plan/%s/' % self.plan_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError:
            assert response.status_code in self.status_codes

    def test_plan_cases(self):
        location = '/plan/%s/cases/' % self.plan_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError:
            assert response.status_code in self.status_codes

    def test_plan_importcase(self):
        location = '/plan/%s/importcase/' % self.plan_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError:
            assert response.status_code in self.status_codes

    def test_plan_delete(self):
        location = '/plan/%s/delete/' % self.plan_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError:
            assert response.status_code in self.status_codes

    def test_plan_searchcase(self):
        location = '/plan/%s/searchcase/' % self.plan_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError:
            assert response.status_code in self.status_codes

    def test_plan_delcase(self):
        location = '/plan/%s/delcase/' % self.plan_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError:
            assert response.status_code in self.status_codes

    def test_plan_ordercase(self):
        location = '/plan/%s/ordercase/' % self.plan_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError:
            assert response.status_code in self.status_codes

    def test_plan_edit(self):
        location = '/plan/%s/edit/' % self.plan_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError:
            assert response.status_code in self.status_codes

    def test_plan_printable(self):
        location = '/plan/%s/printable/' % self.plan_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError:
            assert response.status_code in self.status_codes

    def test_plan_export(self):
        location = '/plan/%s/export/' % self.plan_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError:
            assert response.status_code in self.status_codes

    def test_plan_attachment(self):
        location = '/plan/%s/attachment/' % self.plan_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError:
            assert response.status_code in self.status_codes

    def test_plan_history(self):
        location = '/plan/%s/history/' % self.plan_id
        response = self.c.get(location)
        try:
            self.assertEquals(response.status_code, 200)
        except AssertionError:
            assert response.status_code in self.status_codes


if __name__ == '__main__':
    unittest.main()
