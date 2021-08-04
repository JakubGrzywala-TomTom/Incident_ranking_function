from unittest import TestCase

from scores_calculator import *


class Test(TestCase):

    def test_distance_between_berlin_center_and_wrong_coords(self):
        # given current car position in Berlin center
        berlin_center = (52.52343, 13.41144)
        wrong_coords = ("Error", "Error")

        # when incident corrdinates were not available in TTI output file
        distance = distance_between(berlin_center, wrong_coords)

        # then distance should be -1 (error)
        self.assertEqual(distance, -1)

    def test_distance_between_brandenburg_tor_and_siegessaule(self):
        # given brandenburg_tor and siegessaule coordinates
        brandenburg_tor = (52.51678384995843, 13.377747015342893)
        siegessaule = (52.514606631731546, 13.350163634992205)

        # when counting straight line distance between them
        distance = round(distance_between(brandenburg_tor, siegessaule), 5)

        # then distance rounded to 5 digits after decimal point shoul be 1.88813 km
        self.assertEqual(distance, 1.88813)

    def test_calculate_distance_score_between_brandenburg_tor_and_siegessaule(self):
        # given brandenburg_tor and siegessaule coordinates
        brandenburg_tor = (52.51678384995843, 13.377747015342893)
        siegessaule = (52.514606631731546, 13.350163634992205)

        # when counting straight line distance between them
        # and calucalating distance score basec on distance and outer_radius == 60 km
        distance = distance_between(brandenburg_tor, siegessaule)
        distance_score = calc_distance_score(distance, 60)

        # then distance should be 0.96853
        self.assertEqual(distance_score, 0.96853)

    def test_calculate_distance_score_between_brandenburg_tor_wrong_coords(self):
        # given brandenburg_tor and siegessaule coordinates
        brandenburg_tor = (52.51678384995843, 13.377747015342893)
        wrong_coords = ("Error", "Error")

        # when counting straight line distance between them
        # and calucalating distance score basec on distance and outer_radius == 60 km
        distance = distance_between(brandenburg_tor, wrong_coords)
        distance_score = calc_distance_score(distance, 60)

        # then distance should be 0.96853
        self.assertEqual(distance_score, -100)


    def test_calculate_event_score_when_given_event_not_in_incident(self):
        # given event type categories with scores
        event_categories = {
            "CLOSURE": 1,
            "ROADWORKS": 0.6,
            "ACCIDENT": 1,
        }

        # when an incident did not have any event type info
        # (so get_incident_event function returns "Error")
        event_type_not_available = "Error"
        event_score = calc_event_score(event_type_not_available, event_categories)

        # event_score should be -1
        self.assertEqual(event_score, -1)

    def test_calculate_event_score_when_given_unlisted_event(self):
        # given event type categories with scores
        event_categories = {
            "CLOSURE": 1,
            "ROADWORKS": 0.6,
            "ACCIDENT": 1,
        }

        # when an incident did not have any event type info
        # (so get_incident_event function returns "Error")
        event_type_not_available = "HAZARD"
        event_score = calc_event_score(event_type_not_available, event_categories)

        # event_score should be -1
        self.assertEqual(event_score, 0)

    def test_calculate_event_score_when_given_closure_event(self):
        # given event type categories with scores
        event_categories = {
            "CLOSURE": 1,
            "ROADWORKS": 0.6,
            "ACCIDENT": 1,
        }

        # when an incident did not have any event type info
        # (so get_incident_event function returns "Error")
        event_type_not_available = "CLOSURE"
        event_score = calc_event_score(event_type_not_available, event_categories)

        # event_score should be -1
        self.assertEqual(event_score, 1)
