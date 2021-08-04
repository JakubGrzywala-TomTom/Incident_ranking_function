from unittest import TestCase

from scores_calculator import *


class Test(TestCase):

    # DISTANCE
    def test_distance_between_berlin_center_and_wrong_coords(self):
        # given current car position in Berlin center
        berlin_center = (52.52343, 13.41144)
        wrong_coords = ("Error", "Error")

        # when incident corrdinates were not available in TTI output file
        distance = distance_between(berlin_center, wrong_coords)

        # then distance should be -100 (error)
        self.assertEqual(distance, -100)

    def test_distance_between_brandenburg_tor_and_siegessaule(self):
        # given brandenburg_tor and siegessaule coordinates
        brandenburg_tor = (52.51678384995843, 13.377747015342893)
        siegessaule = (52.514606631731546, 13.350163634992205)

        # when counting straight line distance between them
        distance = round(distance_between(brandenburg_tor, siegessaule), 5)

        # then distance rounded to 5 digits after decimal point should be 1.88813 km
        self.assertEqual(distance, 1.88813)

    # DISTANCE SCORE
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

        # then distance should be -100
        self.assertEqual(distance_score, -100)

    # EVENT SCORE
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

        # event_score should be -100
        self.assertEqual(event_score, -100)

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

        # event_score should be 0
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

        # event_score should be 1
        self.assertEqual(event_score, 1)

    # FRC SCORE
    def test_calculate_frc_score_when_given_error_frc(self):
        # given frc type categories with scores
        frc_categories = {
            "FRC0": 1,
            "FRC1": 0.9,
            "FRC2": 0.8,
        }

        # when an incident did not have any frc type info
        # (so get_incident_frc function returns "Error")
        wrong_frc = "Error"
        frc_score = calc_frc_score(wrong_frc, frc_categories)

        # fcr_score should be -100
        self.assertEqual(frc_score, -100)

    def test_calculate_frc_score_when_given_frc_1(self):
        # given frc type categories with scores
        frc_categories = {
            "FRC0": 1,
            "FRC1": 0.9,
            "FRC2": 0.8,
        }

        # when an incident had FRC1
        wrong_frc = "FRC1"
        frc_score = calc_frc_score(wrong_frc, frc_categories)

        # frc_score should be 0.9
        self.assertEqual(frc_score, 0.9)

    # DELAY SCORE
    def test_calculate_delay_score_when_no_delay(self):
        # given delay type categories with scores
        delay_categories = {
            "300": 0.1,
            "420": 0.2,
            "540": 0.3,
            "660": 0.4,
        }

        # when an incident had no delay info
        wrong_delay = -100
        delay_score = calc_delay_score(wrong_delay, delay_categories)

        # frc_score should be 0
        self.assertEqual(delay_score, 0)

    def test_calculate_delay_score_when_0_delay(self):
        # given delay type categories with scores
        delay_categories = {
            "300": 0.1,
            "420": 0.2,
            "540": 0.3,
            "660": 0.4,
        }

        # when an incident had 0 delay info
        wrong_delay = 0
        delay_score = calc_delay_score(wrong_delay, delay_categories)

        # frc_score should be 0
        self.assertEqual(delay_score, 0.1)

    def test_calculate_delay_score_when_419_delay(self):
        # given delay type categories with scores
        delay_categories = {
            "300": 0.1,
            "420": 0.2,
            "540": 0.3,
            "660": 0.4,
        }

        # when an incident had 419 seconds delay
        wrong_delay = 419
        delay_score = calc_delay_score(wrong_delay, delay_categories)

        # frc_score should be 0.0
        self.assertEqual(delay_score, 0.2)

    # RADIUS BOOST SCORE
    def test_calculate_radius_boost_when_given_error_distance(self):
        # given radius boost categories with scores
        radius_boost_categories = {
            "4": 1,
            "inn_r": 0.5,
            "else": 0
        }

        # when an incident had error distance
        wrong_distance = -100
        inner_radius = 20
        radius_boost_score = calc_radius_boost_score(wrong_distance, inner_radius, radius_boost_categories)

        # radius boost score should be -100
        self.assertEqual(radius_boost_score, -100)

    def test_calculate_radius_boost_when_given_3_distance(self):
        # given radius boost categories with scores
        radius_boost_categories = {
            "4": 1,
            "inn_r": 0.5,
            "else": 0
        }

        # when an incident had 3 km distance to ccp
        wrong_distance = 3
        inner_radius = 20
        radius_boost_score = calc_radius_boost_score(wrong_distance, inner_radius, radius_boost_categories)

        # radius boost score should be 1
        self.assertEqual(radius_boost_score, 1)

    def test_calculate_radius_boost_when_given_15_distance(self):
        # given radius boost categories with scores
        radius_boost_categories = {
            "4": 1,
            "inn_r": 0.5,
            "else": 0
        }

        # when an incident had 15 km distance to ccp
        wrong_distance = 15
        inner_radius = 20
        radius_boost_score = calc_radius_boost_score(wrong_distance, inner_radius, radius_boost_categories)

        # radius boost score should be 0.5
        self.assertEqual(radius_boost_score, 0.5)
