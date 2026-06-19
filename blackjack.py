from machines.shuffle_machine import ShuffleMachine
from roles.player import Player
from utils.judges import judge_blackjack, judge_surrender, judge_split
from utils.trackers import update_properties, track_display_value
from configs.hands_config import MIN_DEALER_VALUE, MAX_TOTAL_VALUE, HANDS_RANGE
from configs.bets_config import MAX_CAPITAL, MIN_BET, MAX_BET, BLACKJACK_PAY
from configs.display_config import DEFAULT_PLAYER_NAME, DANGER_ZONE, MAX_NAME_LEN


class Blackjack:
    def __init__(self):
        self.machine = ShuffleMachine()
        self.round_num = 1

        self.player = Player()
        self.player_name = DEFAULT_PLAYER_NAME
        self.capital = 0
        self.incomes = []

        self._phase = "idle"  # Four scenarios: idle | early_pay | playing | settled.

        self._dealer_cards: list = []
        self._dealer_suits: list = []

        self._dealer_value = 0
        self._dealer_soft = False
        self._dealer_bust = False
        self._dealer_blackjack = False
        self._dealer_early_pay = False

        self._active_hand: str | None = None
        self._active_branch: str | None = None

        self._non_bj_hands: list = []
        self._bj_early_pay_queue: list = []  # BJ hands awaiting take/wait decision.
        self._early_paid_hands: set = set()  # BJ hands that took early pay.

        self._initial_capital = 0
        self._profits: dict = dict()

        # Keys: hand_branch.
        # Values categories:
        # I. Blackjack related: bj | early_pay.
        # II. Out before dealer draws cards: surrendered | bust.
        # III. After dealer gets 17+: won | push | lost.
        self._outcomes: dict = dict()

    def new_session(self, player_name: str, capital: int) -> dict:
        if player_name and len(player_name.strip()) > MAX_NAME_LEN:
            return {"error": f"Name length after stripping left & right spaces must <= {MAX_NAME_LEN}."}

        if capital > MAX_CAPITAL:
            return {"error": f"Capital can't exceed ${MAX_CAPITAL:,}."}

        self.round_num = 1  # Reset for new session.
        self._phase = "idle"

        self.incomes.clear()  # Reset for new session.
        self._bj_early_pay_queue.clear()
        self._early_paid_hands.clear()

        self.player_name = DEFAULT_PLAYER_NAME
        if player_name and player_name.strip():
            self.player_name = player_name.strip()

        self.capital = capital
        return {"capital": self.capital, "player_name": self.player_name}

    def start_round(self, bets: list) -> dict:
        if not bets:
            return {"error": "No bets provided."}

        temp = self.capital
        for bet in bets:
            if bet < MIN_BET:
                return {"error": f"Each bet must be ≥ ${MIN_BET}."}
            
            if bet > MAX_BET:
                return {"error": f"Each bet must be ≤ ${MAX_BET}."}
            
            if bet % 100 != 0:
                return {"error": "Bets must be multiples of $100."}
            
            if bet > temp:
                return {"error": "Insufficient capital for that bet."}
            
            temp -= bet

        if len(bets) > HANDS_RANGE["max"]:
            return {"error": f"Maximum {HANDS_RANGE['max']} hands allowed."}

        self._initial_capital = self.capital
        self.capital = temp
        
        self._profits.clear()  # Reset for new round.
        self._outcomes.clear()
        
        self._bj_early_pay_queue.clear()  # Reset for new round.
        self._early_paid_hands.clear()
        
        self.machine.load_and_shuffle()

        self._dealer_cards.clear()  # Reset for new round.
        self._dealer_suits.clear()

        dealer_card, dealer_suit = self.machine.draw()
        self._dealer_cards.append(dealer_card)
        self._dealer_suits.append(dealer_suit)

        self._dealer_value, self._dealer_soft, _ = update_properties(self._dealer_cards)
        self._dealer_bust = False
        self._dealer_blackjack = False
        self._dealer_early_pay = dealer_card in {"A", "K", "Q", "J", "10"}

        first_two_cards_list = [list(self.machine.draw(True)) for _ in bets]
        self.player.prepare(bets, first_two_cards_list)

        bj_hands = [
            hand_id
            for hand_id in sorted(self.player.hands_dict)
            if self.player.hands_dict[hand_id].blackjack
        ]

        self._non_bj_hands = [
            hand_id
            for hand_id in sorted(self.player.hands_dict)
            if not self.player.hands_dict[hand_id].blackjack
        ]

        if not self._dealer_early_pay:
            # Dealer shows 2-9: auto-pays all BJ hands at 1.5 rate profit immediately.
            for hand_id in bj_hands:
                hand = self.player.hands_dict[hand_id]

                profit = int(hand.initial_chips * BLACKJACK_PAY)
                self.capital += hand.initial_chips + profit

                self._profits[f"{hand_id}_1"] = profit
                self._outcomes[f"{hand_id}_1"] = "bj_auto"
                self._early_paid_hands.add(hand_id)

            self._init_play_phase()

        else:
            # Dealer shows 10/J/Q/K/A: ask BJ player for take/wait decision.
            self._bj_early_pay_queue.extend(bj_hands[:])
            if self._bj_early_pay_queue:
                self._phase = "early_pay"

            else:
                self._init_play_phase()

        return self._serialize()

    def make_early_pay(self, choice: str) -> dict:
        if self._phase != "early_pay" or not self._bj_early_pay_queue:
            return {"error": "No early pay decision pending."}

        hand_id = self._bj_early_pay_queue.pop(0)
        hand = self.player.hands_dict[hand_id]

        if choice == "take":
            # Early pay: 1.0 rate profit. Player gets chips back + equal profit.
            self.capital += hand.initial_chips * 2
            
            self._profits[f"{hand_id}_1"] = hand.initial_chips
            self._outcomes[f"{hand_id}_1"] = "early_pay"
            self._early_paid_hands.add(hand_id)

        # Wait: hand remains. Settled after dealer reveals for 1.5 rate profit or push.
        if self._bj_early_pay_queue:
            self._phase = "early_pay"

        else:
            self._init_play_phase()

        return self._serialize()

    def _init_play_phase(self):
        """Called after all early-pay decisions are made. Routes to insurance, play, or close out."""
        if self._non_bj_hands and self._dealer_cards[0] == "A":
            self._phase = "insurance"
            return

        self._start_playing_or_close()

    def _start_playing_or_close(self):
        """Routes to play phase or closes out. Called after insurance decision (or skipped)."""
        if self._non_bj_hands:
            self._phase = "playing"
            self._active_hand = self._non_bj_hands[0]
            self._active_branch = "1"
            self._auto_skip_21()
            return

        # No non-BJ hands — check if any BJ hands are still waiting for dealer reveal
        bj_waited = [
            hands_id
            for hands_id, hand in self.player.hands_dict.items()
            if hand.blackjack and hands_id not in self._early_paid_hands
        ]

        if bj_waited:
            self._active_hand = None
            self._active_branch = None
            self._dealer_reveal()

        else:
            self._close_round()

    def make_insurance_decision(self, insured_hands: list[str]) -> dict:
        if self._phase != "insurance":
            return {"error": "Not in insurance phase."}

        for hand_id in insured_hands:
            if hand_id in self.player.hands_dict and hand_id in self._non_bj_hands:
                hand = self.player.hands_dict[hand_id]
                insurance = hand.initial_chips // 2

                hand.insurance = insurance
                self.capital -= insurance

        self._start_playing_or_close()
        return self._serialize()

    def hit(self) -> dict:
        if self._phase != "playing" or not self._active_hand:
            return {"error": "Not in playing phase."}

        hand = self.player.hands_dict[self._active_hand]
        card, suit = self.machine.draw()
        hand.hit_or_double_down(card, suit, self._active_branch)

        bust = hand.bust_dict[self._active_branch]
        at_21 = hand.value_dict[self._active_branch] == MAX_TOTAL_VALUE

        if bust or at_21:
            if bust:
                self._outcomes[f"{self._active_hand}_{self._active_branch}"] = "bust"

            if hand.splits > 0:
                card, suit = self.machine.draw()
                hand.reload(card, suit, self._active_branch)

            self._advance_branch()
            self._auto_skip_21()

        return self._serialize()

    def stand(self) -> dict:
        if self._phase != "playing" or not self._active_hand:
            return {"error": "Not in playing phase."}

        hand = self.player.hands_dict[self._active_hand]
        hand.stand(self._active_branch)

        if hand.splits > 0:
            card, suit = self.machine.draw()
            hand.reload(card, suit, self._active_branch)

        self._advance_branch()
        self._auto_skip_21()
        return self._serialize()

    def double_down(self) -> dict:
        if self._phase != "playing" or not self._active_hand:
            return {"error": "Not in playing phase."}

        hand = self.player.hands_dict[self._active_hand]
        self.capital -= hand.initial_chips

        card, suit = self.machine.draw()
        hand.hit_or_double_down(card, suit, self._active_branch, double_down=True)

        if hand.bust_dict[self._active_branch]:
            self._outcomes[f"{self._active_hand}_{self._active_branch}"] = "bust"

        if hand.splits > 0:
            card, suit = self.machine.draw()
            hand.reload(card, suit, self._active_branch)

        self._advance_branch()
        self._auto_skip_21()
        return self._serialize()

    def split(self) -> dict:
        if self._phase != "playing" or not self._active_hand:
            return {"error": "Not in playing phase."}

        hand = self.player.hands_dict[self._active_hand]
        self.capital -= hand.initial_chips

        card, suit = self.machine.draw()
        hand.split(card, suit, self._active_branch)

        if hand.aces_pair:  # No hit nor double down after splitting Aces.
            card, suit = self.machine.draw()
            hand.reload(card, suit, self._active_branch)

            self._advance_branch()  # Branch 1 → branch 2.
            self._advance_branch()  # Branch 2 → next hand / dealer.

        else:
            self._auto_skip_21()

        return self._serialize()

    def surrender(self) -> dict:
        if self._phase != "playing" or not self._active_hand:
            return {"error": "Not in playing phase."}

        hand = self.player.hands_dict[self._active_hand]
        self.capital += hand.initial_chips // 2
        hand.surrender()

        self._outcomes[f"{self._active_hand}_1"] = "surrendered"
        self._profits[f"{self._active_hand}_1"] = -(hand.initial_chips // 2)
        self._advance_hand()
        return self._serialize()

    def _auto_skip_21(self):
        """Auto-advance past any active branch already at value of 21."""
        while self._phase == "playing" and self._active_hand and self._active_branch:
            hand = self.player.hands_dict[self._active_hand]
            branch_id = self._active_branch

            if hand.value_dict.get(branch_id, 0) != MAX_TOTAL_VALUE or hand.bust_dict.get(
                branch_id, False
            ):
                break

            if hand.splits > 0:
                card, suit = self.machine.draw()
                hand.reload(card, suit, branch_id)

            self._advance_branch()

    def _advance_branch(self):
        hand = self.player.hands_dict[self._active_hand]
        branches = list(hand.cards_dict.keys())

        if self._active_branch == branches[-1]:
            self._advance_hand()

        else:
            idx = branches.index(self._active_branch)
            self._active_branch = branches[idx + 1]

    def _advance_hand(self):
        if self._active_hand == self._non_bj_hands[-1]:
            self._dealer_reveal()

        else:
            idx = self._non_bj_hands.index(self._active_hand)
            self._active_hand = self._non_bj_hands[idx + 1]
            self._active_branch = "1"

    def _needs_dealer_draw(self) -> bool:
        """True if at least one hand requires the dealer to draw cards."""
        for hand_id, hand in self.player.hands_dict.items():
            if hand.blackjack and hand_id not in self._early_paid_hands:
                return True  # BJ hand that chose to wait needs dealer reveal.

        for hand_id in self._non_bj_hands:
            hand = self.player.hands_dict[hand_id]
            if hand.surrendered:
                continue

            for branch_id in hand.cards_dict:
                if not hand.bust_dict.get(branch_id, False):
                    return True  # Non-busted branch needs dealer reveal.

        return False

    def _dealer_reveal(self):
        if not self._needs_dealer_draw():
            self._settle()
            return

        check_bj_only = self._all_non_bj_finished()

        while self._dealer_value < MIN_DEALER_VALUE:
            card, suit = self.machine.draw()
            self._dealer_cards.append(card)
            self._dealer_suits.append(suit)

            if judge_blackjack(self._dealer_cards):
                self._dealer_blackjack = True
                break

            if check_bj_only:
                break

            value, soft, bust = update_properties(self._dealer_cards)
            self._dealer_value = value
            self._dealer_soft = soft

            if bust:
                self._dealer_value = 0  # 0 means dealer is busted.
                self._dealer_bust = True
                break

        self._settle()

    def _all_non_bj_finished(self) -> bool:
        """True when the dealer only needs to expose for a BJ check."""
        if not self._non_bj_hands:
            return True

        for hand_id in self._non_bj_hands:
            hand = self.player.hands_dict[hand_id]
            if hand.surrendered:
                continue

            if all(hand.bust_dict.get(b, False) for b in hand.cards_dict):
                continue

            return False

        return True

    def _settle(self):
        for hand_id, hand in self.player.hands_dict.items():
            if hand_id in self._early_paid_hands:
                continue  # Already paid profits.

            if hand.surrendered:
                continue  # Already took away 50% of bets.

            if hand.blackjack:
                key = f"{hand_id}_1"
                if self._dealer_blackjack:
                    payout, profit = hand.initial_chips, 0
                    self._outcomes[key] = "push"

                else:
                    profit = int(hand.initial_chips * BLACKJACK_PAY)
                    payout = hand.initial_chips + profit
                    self._outcomes[key] = "bj"

                self.capital += payout
                self._profits[key] = profit
                continue

            for branch_id in hand.cards_dict:
                key = f"{hand_id}_{branch_id}"
                chips = hand.chips_dict.get(branch_id, hand.initial_chips)

                bust = hand.bust_dict.get(branch_id, False)
                value = hand.value_dict.get(branch_id, 0)

                if bust:
                    payout, profit = 0, -chips
                    self._outcomes[key] = "bust"

                elif self._dealer_blackjack:
                    payout, profit = 0, -chips
                    self._outcomes[key] = "lost"

                elif self._dealer_bust or value > self._dealer_value:
                    payout, profit = chips * 2, chips
                    self._outcomes[key] = "won"

                elif value == self._dealer_value:
                    payout, profit = chips, 0
                    self._outcomes[key] = "push"

                else:
                    payout, profit = 0, -chips
                    self._outcomes[key] = "lost"

                self.capital += payout
                self._profits[key] = profit

        # Insurance pays 2.0 rate profit if dealer has blackjack.
        for hand_id, hand in self.player.hands_dict.items():
            if hand.insurance > 0 and self._dealer_blackjack:
                self.capital += hand.insurance * 3

        self._close_round()

    def _close_round(self):
        total_profit = self.capital - self._initial_capital
        self.incomes.append(
            {
                "Round": self.round_num,
                "Profit": total_profit,
                "Capital": self.capital,
            }
        )

        self.round_num += 1
        self._phase = "settled"

        self._active_hand = None
        self._active_branch = None

    def _serialize(self) -> dict:
        dealer_data = {
            "cards": [
                {"rank": card, "suit": suit}
                for card, suit in zip(self._dealer_cards, self._dealer_suits)
            ],
            "face_down": False,  # Macau: dealer never deals a hole card.
            "value_text": self._dealer_value_text(),
            "blackjack": self._dealer_blackjack,
            "bust": self._dealer_bust,
            "early_pay": self._dealer_early_pay,
        }

        hands = []
        for hand_id in sorted(self.player.hands_dict.keys()):
            hand = self.player.hands_dict[hand_id]
            branches = []

            for branch_id in hand.cards_dict:
                key = f"{hand_id}_{branch_id}"

                cards = [
                    {"rank": card, "suit": suit}
                    for card, suit in zip(hand.cards_dict[branch_id], hand.suits_dict[branch_id])
                ]

                branch_value = hand.value_dict.get(branch_id, 0)
                is_soft = hand.soft_dict.get(branch_id, False)
                is_bust = hand.bust_dict.get(branch_id, False)

                # A branch is finalized when it no longer accepts player input.
                # Like: settled, busted, surrendered, doubled-down, or positionally past.
                is_finalized = (
                    self._phase == "settled"
                    or is_bust
                    or hand.surrendered
                    or hand.double_down_dict.get(branch_id, False)
                )

                if not is_finalized and self._phase == "playing" and self._active_hand:
                    try:
                        hand_pos = self._non_bj_hands.index(hand_id)
                        active_pos = self._non_bj_hands.index(self._active_hand)
                        if hand_pos < active_pos:
                            is_finalized = True

                        elif hand_pos == active_pos and self._active_branch:
                            b_list = list(hand.cards_dict.keys())
                            is_finalized = b_list.index(branch_id) < b_list.index(
                                self._active_branch
                            )

                    except ValueError:
                        pass

                if hand.blackjack and branch_id == "1":
                    value_text = "Blackjack"

                elif hand.surrendered and branch_id == "1":
                    value_text = "Surrender"

                else:
                    value_text = track_display_value(
                        branch_value,
                        soft=is_soft,
                        bust=is_bust,
                        stand=is_finalized,
                    )

                is_active = (
                    self._phase == "playing"
                    and hand_id == self._active_hand
                    and branch_id == self._active_branch
                )

                outcome = self._outcomes.get(
                    key, self._default_outcome(hand_id, branch_id, hand, is_active)
                )

                # When players' value is inside hard 12~16.
                is_danger = (
                    not hand.surrendered
                    and not is_soft
                    and DANGER_ZONE["lower"] <= branch_value <= DANGER_ZONE["upper"]
                )

                branches.append(
                    {
                        "id": branch_id,
                        "cards": cards,
                        "value_text": value_text,
                        "bet": hand.chips_dict.get(branch_id, hand.initial_chips),
                        "bust": is_bust,
                        "active": is_active,
                        "outcome": outcome,
                        "danger": is_danger,
                        "profit": self._profits.get(key),
                        "is_aces_split": hand.aces_pair,
                    }
                )

            label = f"Hand {hand_id}" + (" · Split" if hand.splits > 0 else "")
            hands.append(
                {
                    "id": hand_id,
                    "label": label,
                    "splits": hand.splits,
                    "blackjack": hand.blackjack,
                    "surrendered": hand.surrendered,
                    "branches": branches,
                }
            )

        result = {
            "phase": self._phase,
            "capital": self.capital,
            "dealer": dealer_data,
            "hands": hands,
            "round": self.round_num,
        }

        if self._phase == "playing" and self._active_hand:
            result["active_hand"] = self._active_hand
            result["active_branch"] = self._active_branch
            result["moves"] = self._available_moves()

        if self._phase == "insurance":
            result["insurance_hands"] = [
                {
                    "hand_id": hands_id,
                    "insurance_amount": self.player.hands_dict[hands_id].initial_chips // 2,
                }
                for hands_id in self._non_bj_hands
            ]

        if self._phase == "early_pay" and self._bj_early_pay_queue:
            pending = self._bj_early_pay_queue[0]
            result["early_pay_hand"] = pending
            result["early_pay_chips"] = self.player.hands_dict[pending].initial_chips

        return result

    def _default_outcome(self, hand_id: str, branch_id: str, hand, is_active: bool) -> str:
        """Outcome for branches not yet in _outcomes dict."""
        if hand.blackjack and branch_id == "1":
            if hand_id in self._bj_early_pay_queue:
                return "bj_pending"  # BJ waiting for take/wait decision.

            return "idle"  # Waited BJ is waiting for dealer to reveal.

        return "active" if is_active else "idle"

    def _dealer_value_text(self) -> str:
        if self._phase in ("playing", "early_pay", "insurance"):
            return self._dealer_cards[0]  # Show only dealer's 1st card.

        if len(self._dealer_cards) == 1:  # Dealer didn't draw cards: all hands are settled.
            return self._dealer_cards[0]

        if self._dealer_blackjack:
            return "Blackjack"

        if self._dealer_bust:
            bust_val, _, _ = update_properties(self._dealer_cards)
            return f"{bust_val} — Busted"

        return track_display_value(
            self._dealer_value, dealer=True, soft=self._dealer_soft
        )

    def _available_moves(self) -> list:
        hand = self.player.hands_dict[self._active_hand]
        cards = hand.cards_dict[self._active_branch]
        moves = ["hit", "stand"]

        if judge_surrender(cards, self._dealer_cards[0], hand.splits):
            moves.append("surrender")

        if len(cards) == 2 and self.capital >= hand.initial_chips:
            moves.append("double")

        if judge_split(cards, hand.splits) and self.capital >= hand.initial_chips:
            moves.append("split")

        return moves

    def get_incomes(self) -> list:
        return self.incomes
