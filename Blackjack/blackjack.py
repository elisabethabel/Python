"""Simple game of blackjack."""
from textwrap import dedent

import requests


class Card:
    """Simple dataclass for holding card information."""

    def __init__(self, value: str, suit: str, code: str):
        """Class constructor. Each card has value, suit and code."""
        self.value = value
        self.suit = suit
        self.code = code

    def __repr__(self) -> str:
        """Product object representation in object format."""
        return self.code


class Hand:
    """Simple class for holding hand information."""

    def __init__(self):
        """Class constructor. Each hand has cards and score."""
        self.score = 0
        self.cards = []
        self.aces = 0

    def add_card(self, card: Card):
        """Add card to cards list and calculate score."""
        card_values = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
                       "10": 10, "JACK": 10, "QUEEN": 10, "KING": 10, "ACE": 11}
        if card.value == "ACE":
            self.aces += 1
        self.score += card_values[card.value]
        self.cards.append(card)
        while self.score > 21 and self.aces > 0:
            self.score -= 10
            self.aces -= 1


class Deck:
    """Deck of cards. Provided via api over the network."""

    def __init__(self, shuffle=False):
        """Make new deck."""
        if not shuffle:
            self.deck = requests.get("https://deckofcardsapi.com/api/deck/new").json()
            self.is_shuffled = False
        else:
            self.deck = requests.get("https://deckofcardsapi.com/api/deck/new/shuffle").json()
            self.is_shuffled = True
        self.deck_id = self.deck["deck_id"]

    def shuffle(self):
        """Shuffle the deck."""
        self.deck = requests.get(f"https://deckofcardsapi.com/api/deck/{self.deck_id}/shuffle").json()
        self.is_shuffled = True

    def draw(self) -> Card:
        """Draw card from the deck."""
        result = requests.get(f"https://deckofcardsapi.com/api/deck/{self.deck_id}/draw").json()
        result = Card(result["cards"][0]["value"], result["cards"][0]["suit"], result["cards"][0]["code"])
        return result


class BlackjackController:
    """Blackjack controller. For controlling the game and data flow between view and database."""

    def __init__(self, deck: Deck, view: 'BlackjackView'):
        """Blackjack controller. For controlling the game and data flow between view and database."""
        if not deck.is_shuffled:
            deck.shuffle()
        self.player_hand = Hand()
        self.dealer_hand = Hand()
        self.draw_first_cards(deck)
        self.state = {"dealer": self.dealer_hand, "player": self.player_hand}
        if self.player_hand.score == 21:
            view.player_won(self.state)
            return
        self.player_moves(deck, view)
        if self.player_hand.score == 21:
            view.player_won(self.state)
            return
        if self.player_hand.score > 21 or self.dealer_hand.score == 21:
            view.player_lost(self.state)
            return
        self.dealer_moves(deck)
        if self.dealer_hand.score > 22:
            view.player_won(self.state)
            return
        if self.dealer_hand.score > self.player_hand.score:
            view.player_lost(self.state)

    def draw_first_cards(self, deck: Deck):
        """Draw first four cards from deck."""
        for _ in range(2):
            self.player_hand.add_card(deck.draw())
            self.dealer_hand.add_card(deck.draw())

    def player_moves(self, deck: Deck, view: 'BlackjackView'):
        """Move for player."""
        while self.player_hand.score < 21 and view.ask_next_move(self.state) == "H":
            self.player_hand.add_card(deck.draw())

    def dealer_moves(self, deck: Deck):
        """Move for dealer."""
        while self.dealer_hand.score < self.player_hand.score:
            self.dealer_hand.add_card(deck.draw())


class BlackjackView:
    """Minimalistic UI/view for the blackjack game."""

    def ask_next_move(self, state: dict) -> str:
        """
        Get next move from the player.

        :param state: dict with given structure: {"dealer": dealer_hand_object, "player": player_hand_object}
        :return: parsed command that user has choses. String "H" for hit and "S" for stand
        """
        self.display_state(state)
        while True:
            action = input("Vali oma järgmine käik: Jätka(H), lõpeta(S) > ")
            if action.upper() in ["H", "S"]:
                return action.upper()
            print("Invalid command!")

    def player_lost(self, state):
        """
        Display player lost dialog to the user.

        :param state: dict with given structure: {"dealer": dealer_hand_object, "player": player_hand_object}
        """
        self.display_state(state, final=True)
        print("You lost")

    def player_won(self, state):
        """
        Display player won dialog to the user.

        :param state: dict with given structure: {"dealer": dealer_hand_object, "player": player_hand_object}
        """
        self.display_state(state, final=True)
        print("You won")

    def display_state(self, state, final=False):
        """
        Display state of the game for the user.

        :param state: dict with given structure: {"dealer": dealer_hand_object, "player": player_hand_object}
        :param final: boolean if the given state is final state. True if game has been lost or won.
        """
        dealer_score = state["dealer"].score if final else "??"
        dealer_cards = state["dealer"].cards
        if not final:
            dealer_cards_hidden_last = [c.__repr__() for c in dealer_cards[:-1]] + ["??"]
            dealer_cards = f"[{','.join(dealer_cards_hidden_last)}]"

        player_score = state["player"].score
        player_cards = state["player"].cards
        print(dedent(
            f"""
            {"Dealer score":<15}: {dealer_score}
            {"Dealer hand":<15}: {dealer_cards}

            {"Your score":<15}: {player_score}
            {"Your hand":<15}: {player_cards}
            """
        ))


if __name__ == '__main__':
    BlackjackController(Deck(), BlackjackView())  # start the game.
