import unittest
from unittest.mock import patch
from blackjack import Blackjack
from configs.bets_config import MIN_BET, MAX_BET


class TestNewSession(unittest.TestCase):
    """Test Blackjack.new_session initializes session state."""

    def setUp(self):
        self.app = Blackjack()

    def test_set_capital(self):
        result = self.app.new_session("Alice", 10000)
        self.assertEqual(result["capital"], 10000)
        self.assertEqual(self.app.capital, 10000)

    def test_set_player_name(self):
        result = self.app.new_session("Alice", 10000)
        self.assertEqual(result["player_name"], "Alice")

    def test_strip_boundary_whitespace(self):
        result = self.app.new_session("  Bob  ", 5000)
        self.assertEqual(result["player_name"], "Bob")

    def test_blank_name_processing(self):
        result = self.app.new_session("   ", 5000)
        self.assertTrue(len(result["player_name"]) > 0)
        self.assertNotEqual(result["player_name"], "   ")

    def test_new_session_round_reset(self):
        self.app.new_session("Alice", 10000)
        self.assertEqual(self.app.round_num, 1)
        self.assertEqual(self.app.incomes, [])


class TestStartRoundValidation(unittest.TestCase):
    """Test Blackjack.start_round rejects invalid bet configurations."""

    def setUp(self):
        self.app = Blackjack()
        self.app.new_session("Alice", 10000)

    def test_empty_bets_error(self):
        result = self.app.start_round([])
        self.assertIn("error", result)

    def test_bet_range_number_error(self):
        result = self.app.start_round([MIN_BET - 100])
        self.assertIn("error", result)

        result = self.app.start_round([MAX_BET + 100])
        self.assertIn("error", result)

        result = self.app.start_round([350])
        self.assertIn("error", result)

    def test_excessive_hands_error(self):
        result = self.app.start_round([300] * 7)
        self.assertIn("error", result)

    def test_insufficient_capital_error(self):
        self.app.capital = 400
        result = self.app.start_round([500])
        self.assertIn("error", result)

    def test_valid_bet_clears_error(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('6', 'S'),
                 ('7', '8', 'D', 'H'),
             ]):
            result = self.app.start_round([500])

        self.assertNotIn("error", result)


class TestPlayerBusts(unittest.TestCase):
    """Player hits into a bust — dealer skips reveal, round settles immediately."""

    def setUp(self):
        self.app = Blackjack()
        self.app.new_session("Alice", 10000)

    def test_phase_is_settled(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('6', 'S'),            # Dealer 1st card is 6.
                 ('7', '8', 'D', 'H'),  # Player has 7 + 8 = 15.
                 ('K', 'C'),            # Player hits K: 15 becomes busted 25.
             ]):

            self.app.start_round([500])
            result = self.app.hit()

        self.assertEqual(result["phase"], "settled")

    def test_busted_outcome(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('6', 'S'),
                 ('9', '8', 'D', 'H'),
                 ('K', 'C'),
             ]):

            self.app.start_round([500])
            result = self.app.hit()

        outcome = result["hands"][0]["branches"][0]["outcome"]
        self.assertEqual(outcome, "bust")

    def test_capital_reduction(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('6', 'S'),
                 ('9', '8', 'D', 'H'),
                 ('K', 'C'),
             ]):

            self.app.start_round([500])
            self.app.hit()

        self.assertEqual(self.app.capital, 9500)

    def test_income_records_loss_entry(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('6', 'S'),
                 ('9', '8', 'D', 'H'),
                 ('K', 'C'),
             ]):

            self.app.start_round([500])
            self.app.hit()

        self.assertEqual(len(self.app.incomes), 1)
        self.assertEqual(self.app.incomes[0]["Profit"], -500)


class TestPlayerWinsDealerBusts(unittest.TestCase):
    """Player is not busted and dealer draws into bust: player wins."""

    def setUp(self):
        self.app = Blackjack()
        self.app.new_session("Alice", 10000)

    def _run_round(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('6', 'S'),            # Dealer 1st card is 6.
                 ('9', '8', 'D', 'H'),  # Player has 9 + 8 = 17.
                 ('8', 'C'),            # Dealer draws 8: 6 becomes 14.
                 ('9', 'D'),            # Dealer draws 9: 14 becomes busted 23.
             ]):

            self.app.start_round([500])
            return self.app.stand()

    def test_phase_is_settled(self):
        result = self._run_round()
        self.assertEqual(result["phase"], "settled")

    def test_winning_outcome(self):
        result = self._run_round()
        outcome = result["hands"][0]["branches"][0]["outcome"]
        self.assertEqual(outcome, "won")

    def test_capital_increment(self):
        self._run_round()
        self.assertEqual(self.app.capital, 10500)

    def test_dealer_bust_flag(self):
        self._run_round()
        self.assertTrue(self.app._dealer_bust)

    def test_income_records_profit_entry(self):
        self._run_round()
        self.assertEqual(self.app.incomes[0]["Profit"], 500)


class TestPush(unittest.TestCase):
    """Player and dealer finish with equal values — push."""

    def setUp(self):
        self.app = Blackjack()
        self.app.new_session("Alice", 10000)

    def _run_round(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('6', 'S'),            # Dealer 1st card is 6.
                 ('K', '9', 'D', 'H'),  # Player has K + 9 = 19.
                 ('K', 'C'),            # Dealer draws K: 6 becomes 16.
                 ('3', 'D'),            # Dealer draws 3: 16 becomes 19.
             ]):

            self.app.start_round([500])
            return self.app.stand()

    def test_push_outcome(self):
        result = self._run_round()
        outcome = result["hands"][0]["branches"][0]["outcome"]
        self.assertEqual(outcome, "push")

    def test_capital_unchanged(self):
        self._run_round()
        self.assertEqual(self.app.capital, 10000)

    def test_profit_is_zero(self):
        self._run_round()
        self.assertEqual(self.app.incomes[0]["Profit"], 0)


class TestBlackjackAutoPay(unittest.TestCase):
    """Dealer 1st has no BJ chance: player's BJ is auto-paid at 1.5 rate profit immediately."""

    def setUp(self):
        self.app = Blackjack()
        self.app.new_session("Alice", 10000)

    def _run_round(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('6', 'S'),            # Dealer 1st card is 9.
                 ('A', 'K', 'D', 'H'),  # Player has A + K = Blackjack.
             ]):

            return self.app.start_round([500])

    def test_phase_is_settled_immediately(self):
        result = self._run_round()
        self.assertEqual(result["phase"], "settled")

    def test_auto_paid_bj_outcome(self):
        result = self._run_round()
        outcome = result["hands"][0]["branches"][0]["outcome"]
        self.assertEqual(outcome, "bj_auto")

    def test_capital_reflects_3_to_2_profit(self):  # 3 / 2 = 1.5.
        self._run_round()
        self.assertEqual(self.app.capital, 10750)  # 9500 + 500 * (1 + 1.5).

    def test_3_to_2_profit(self):
        self._run_round()
        self.assertEqual(self.app.incomes[0]["Profit"], 750)


class TestEarlyPayTake(unittest.TestCase):
    """Dealer might get BJ: player has BJ and takes early pay of 1.0 profit."""

    def setUp(self):
        self.app = Blackjack()
        self.app.new_session("Alice", 10000)

    def _run_round(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('A', 'S'),            # Dealer 1st card is A.
                 ('A', 'K', 'D', 'H'),  # Player has A + K: Blackjack.
             ]):

            self.app.start_round([500])

        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[]):
            return self.app.make_early_pay_decision("take")

    def test_phase_becomes_settled(self):
        result = self._run_round()
        self.assertEqual(result["phase"], "settled")

    def test_early_paid_outcome(self):
        result = self._run_round()
        outcome = result["hands"][0]["branches"][0]["outcome"]
        self.assertEqual(outcome, "early_pay")

    def test_capital_reflects_unit_profit(self):
        self._run_round()
        self.assertEqual(self.app.capital, 10500)  # 9500 + 500 * (1 + 1).

    def test_unit_profit(self):
        self._run_round()
        self.assertEqual(self.app.incomes[0]["Profit"], 500)

    def test_phase_is_marked_early_pay(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('A', 'S'),
                 ('A', 'K', 'D', 'H'),
             ]):
            result = self.app.start_round([500])

        self.assertEqual(result["phase"], "early_pay")


class TestEarlyPayWaitDealerBlackjack(unittest.TestCase):
    """Player waits on early pay and dealer also has BJ: push."""

    def setUp(self):
        self.app = Blackjack()
        self.app.new_session("Alice", 10000)

    def _run_round(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('A', 'S'),            # Dealer 1st card is A.
                 ('A', 'K', 'D', 'H'),  # Player has A + K: Blackjack.
                 ('K', 'C'),            # Dealer has A + K: Blackjack.
             ]):

            self.app.start_round([500])
            return self.app.make_early_pay_decision("wait")

    def test_phase_is_settled(self):
        result = self._run_round()
        self.assertEqual(result["phase"], "settled")

    def test_push_outcome(self):
        result = self._run_round()
        outcome = result["hands"][0]["branches"][0]["outcome"]
        self.assertEqual(outcome, "push")

    def test_capital_unchanged(self):
        self._run_round()
        self.assertEqual(self.app.capital, 10000)

    def test_dealer_blackjack_flag(self):
        self._run_round()
        self.assertTrue(self.app._dealer_blackjack)


class TestSurrender(unittest.TestCase):
    """Player surrenders a two-card hand: loses 50% of the bet."""

    def setUp(self):
        self.app = Blackjack()
        self.app.new_session("Alice", 10000)

    def _run_round(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('J', 'S'),            # Dealer 1st card is J.
                 ('Q', '6', 'D', 'H'),  # Player has Q + 6 = 16.
             ]):

            self.app.start_round([500])
            return self.app.surrender()

    def test_phase_is_settled(self):
        result = self._run_round()
        self.assertEqual(result["phase"], "settled")

    def test_surrendered_outcome(self):
        result = self._run_round()
        outcome = result["hands"][0]["branches"][0]["outcome"]
        self.assertEqual(outcome, "surrendered")

    def test_capital_reflects_returned_bet(self):
        self._run_round()
        self.assertEqual(self.app.capital, 9750)  # 9500 + 500 / 2.

    def test_half_loss(self):
        self._run_round()
        self.assertEqual(self.app.incomes[0]["Profit"], -250)

    def test_surrender_in_available_moves(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('J', 'S'),
                 ('Q', '6', 'D', 'H'),
             ]):

            result = self.app.start_round([500])

        self.assertIn("surrender", result["moves"])


class TestDoubleDown(unittest.TestCase):
    """Player doubles down; wins against dealer who doesn't bust."""

    def setUp(self):
        self.app = Blackjack()
        self.app.new_session("Alice", 10000)

    def _run_round(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('8', 'S'),            # Dealer 1st card is 8.
                 ('5', '6', 'D', 'H'),  # Player has 5 + 6 = 11.
                 ('K', 'C'),            # Double down draws K: 11 becomes 21.
                 ('Q', 'C'),            # Dealer draws Q: 8 becomes 18.
             ]):

            self.app.start_round([500])
            return self.app.double_down()

    def test_phase_is_settled(self):
        result = self._run_round()
        self.assertEqual(result["phase"], "settled")

    def test_winning_outcome(self):
        result = self._run_round()
        outcome = result["hands"][0]["branches"][0]["outcome"]
        self.assertEqual(outcome, "won")

    def test_bet_doubled(self):
        result = self._run_round()
        self.assertEqual(result["hands"][0]["branches"][0]["bet"], 1000)

    def test_capital_reflects_correct_profit(self):
        self._run_round()

        # Capital after placing initial bet: 9500.
        # After doubling bet for double down: 9000.
        # Won 1000 chips: 9000 + 2000 = 11000.

        self.assertEqual(self.app.capital, 11000)

    def test_correct_profit(self):
        self._run_round()
        self.assertEqual(self.app.incomes[0]["Profit"], 1000)

    def test_double_down_in_available_moves(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('8', 'S'),
                 ('5', '6', 'D', 'H'),
             ]):

            result = self.app.start_round([500])

        self.assertIn("double", result["moves"])


class TestSplit(unittest.TestCase):
    """Player splits a pair. Both branches play out against dealer."""

    def setUp(self):
        self.app = Blackjack()
        self.app.new_session("Alice", 10000)

    def _run_round(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('5', 'S'),            # Dealer 1st card is 5.
                 ('8', '8', 'D', 'H'),  # Player has 8 + 8 pair.
                 ('J', 'C'),            # Player splits: branch 1 = 8 + J = 18.
                 ('5', 'D'),            # Reload branch 2 to 8 + 5 = 13.
                 ('2', 'S'),            # Ineffective reload: branch 3 doesn't exist.
                 ('J', 'C'),            # Dealer draws J: 5 becomes 15.
                 ('4', 'H'),            # Dealer draws 4: 15 becomes 19.
             ]):

            self.app.start_round([500])
            self.app.split()
            self.app.stand()           # Stand on branch 1 w/ value 18.
            return self.app.stand()    # Stand on branch 2 w/ value 13.

    def test_phase_is_settled(self):
        result = self._run_round()
        self.assertEqual(result["phase"], "settled")

    def test_two_branches_created(self):
        result = self._run_round()
        self.assertEqual(len(result["hands"][0]["branches"]), 2)

    def test_split_counter(self):
        self._run_round()
        hand = self.app.player.hands_dict['1']
        self.assertEqual(hand.splits, 1)

    def test_capital_reduction(self):
        self._run_round()

        # Capital after placing initial bet: 9500.
        # Split deducts another 500: 9000.
        # Both branches lose to dealer 19.

        self.assertEqual(self.app.capital, 9000)

    def test_both_branches_lose(self):
        result = self._run_round()
        branches = result["hands"][0]["branches"]

        self.assertEqual(branches[0]["outcome"], "lost")
        self.assertEqual(branches[1]["outcome"], "lost")

    def test_split_in_available_moves(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('5', 'S'),
                 ('8', '8', 'D', 'H'),
             ]):

            result = self.app.start_round([500])

        self.assertIn("split", result["moves"])


class TestInsurance(unittest.TestCase):
    """Insurance phase: dealer shows Ace, player may bet against dealer blackjack."""

    def setUp(self):
        self.app = Blackjack()
        self.app.new_session("Alice", 10000)

    def test_insurance_phase_against_dealer_ace(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('A', 'S'),            # Dealer 1st card is A.
                 ('7', '8', 'D', 'H'),  # Player doesn't have BJ.
             ]):

            result = self.app.start_round([500])

        self.assertEqual(result["phase"], "insurance")

    def test_insurance_hands(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('A', 'S'),
                 ('7', '8', 'D', 'H'),
             ]):
            result = self.app.start_round([500])

        self.assertEqual(len(result["insurance_hands"]), 1)
        self.assertEqual(result["insurance_hands"][0]["hand_id"], "1")
        self.assertEqual(result["insurance_hands"][0]["insurance_amount"], 250)  # 500 / 2.

    def test_capital_deduction(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('A', 'S'),
                 ('7', '8', 'D', 'H'),
             ]):

            self.app.start_round([500])

        self.app.make_insurance_decision(['1'])
        self.assertEqual(self.app.capital, 9250)  # 9500 - 250.

    def test_no_insurance_capital(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('A', 'S'),
                 ('7', '8', 'D', 'H'),
             ]):

            self.app.start_round([500])

        self.app.make_insurance_decision([])
        self.assertEqual(self.app.capital, 9500)

    def test_phase_after_insurance_decision(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('A', 'S'),
                 ('7', '8', 'D', 'H'),
             ]):

            self.app.start_round([500])

        result = self.app.make_insurance_decision(['1'])
        self.assertEqual(result["phase"], "playing")

    def test_insurance_pays_2_to_1_against_dealer_blackjack(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('A', 'S'),            # Dealer 1st card is A.
                 ('10', '8', 'D', 'H'),  # Player doesn't have BJ and buys insurance.
                 ('10', 'C'),           # Dealer draws 10: Ace + 10 = Blackjack.
             ]):

            self.app.start_round([500])
            self.app.make_insurance_decision(['1'])
            result = self.app.stand()

        # 10000 - 500 (bet) - 250 (insurance) = 9250.
        # Bet was lost.
        # Insurance won so returned money is 250 * (1 + 2) = 750. Insurance profit pays 2:1.
        # 9250 + 750 = 10000.

        self.assertEqual(self.app.capital, 10000)
        self.assertEqual(result["phase"], "settled")

    def test_lost_hand_against_dealer_blackjack(self):
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('A', 'S'),
                 ('7', '8', 'D', 'H'),
                 ('10', 'C'),
             ]):

            self.app.start_round([500])
            self.app.make_insurance_decision(['1'])
            result = self.app.stand()

        self.assertEqual(result["hands"][0]["branches"][0]["outcome"], "lost")

    def test_lost_insurance_when_dealer_has_no_blackjack(self):
        with (
            patch.object(self.app.machine, "load_and_shuffle"),
            patch.object(
                self.app.machine,
                "draw",
                side_effect=[
                    ("A", "S"),  # Dealer 1st card is A.
                    ("7", "8", "D", "H"),  # Player doesn't have BJ and buys insurance.
                    ("9", "C"),  # Dealer draws 9: A + 9. No BJ.
                ],
            ),
        ):
            
            self.app.start_round([500])
            self.app.make_insurance_decision(['1'])
            result = self.app.stand()

        # 10000 - 500 (bet) - 250 (insurance) = 9250.
        # Bet and insurance were all lost.

        self.assertEqual(self.app.capital, 9250)
        self.assertEqual(result["phase"], "settled")

    def test_insurance_skipped_when_all_hands_are_blackjack(self):
        """Dealer shows Ace but all player hands are BJ: goes to early pay, not insurance."""
        with patch.object(self.app.machine, 'load_and_shuffle'), \
             patch.object(self.app.machine, 'draw', side_effect=[
                 ('A', 'S'),            # Dealer 1st card is Ace.
                 ('A', 'K', 'D', 'H'),  # Player has Blackjack.
             ]):

            result = self.app.start_round([500])

        self.assertEqual(result["phase"], "early_pay")
        self.assertNotIn("insurance_hands", result)

    def test_make_insurance_decision_errors_outside_insurance_phase(self):
        result = self.app.make_insurance_decision(['1'])
        self.assertIn("error", result)


class TestMultipleRounds(unittest.TestCase):
    """Capital and round counter carry over across consecutive rounds."""

    def setUp(self):
        self.app = Blackjack()
        self.app.new_session("Alice", 10000)

    def test_round_number_increments(self):
        for draws in [
            [('9', 'S'), ('9', '5', 'D', 'H'), ('K', 'C')],  # Round 1: bust.
            [('9', 'S'), ('9', '4', 'D', 'H'), ('K', 'C')],  # Round 2: bust.
        ]:
            with patch.object(self.app.machine, 'load_and_shuffle'), \
                 patch.object(self.app.machine, 'draw', side_effect=draws):
                self.app.start_round([500])
                self.app.hit()

        self.assertEqual(self.app.round_num, 3)

    def test_incomes_accumulate_across_rounds(self):
        for draws in [
            [('9', 'S'), ('9', '5', 'D', 'H'), ('K', 'C')],  # Round 1: bust.
            [('9', 'S'), ('9', '4', 'D', 'H'), ('K', 'C')],  # Round 2: bust.
        ]:
            with patch.object(self.app.machine, 'load_and_shuffle'), \
                 patch.object(self.app.machine, 'draw', side_effect=draws):

                self.app.start_round([500])
                self.app.hit()

        self.assertEqual(len(self.app.incomes), 2)

    def test_capital_carries_between_rounds(self):
        for draws in [
            [('6', 'S'), ('9', '8', 'D', 'H'), ('K', 'C')],
            [('6', 'S'), ('9', '8', 'D', 'H'), ('K', 'C')],
        ]:
            with patch.object(self.app.machine, 'load_and_shuffle'), \
                 patch.object(self.app.machine, 'draw', side_effect=draws):

                self.app.start_round([500])
                self.app.hit()

        self.assertEqual(self.app.capital, 9000)  # Lost 500 twice.


if __name__ == '__main__':
    unittest.main()
