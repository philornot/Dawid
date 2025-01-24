from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable
import json
import re
import random
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
import math


class ConversationState(Enum):
    NORMAL = "normal"
    LEARNING = "learning"
    CALCULATING = "calculating"


@dataclass
class Interaction:
    question: str
    answer: str
    timestamp: str
    learned: bool = False


class ESFJPersonality:
    GREETING_TEMPLATES = [
        "Hej! 😊",
        "Cześć!",
        "Dzień dobry! 👋",
        "Siema!",
        "Witaj! ✨",
        "Co słychać? 😊"
    ]

    LEARNING_TEMPLATES = [
        "Nie wiem, nauczysz mnie? 🤔",
        "Pierwsze słyszę! Co to?",
        "Opowiesz mi o tym? 😊",
        "A co to takiego?",
        "Nie znam tego jeszcze!",
        "Wyjaśnisz? 🤗"
    ]

    GRATITUDE_TEMPLATES = [
        "Dzięki! 💖",
        "Super, że mi powiedziałeś!",
        "O, fajnie! 😊",
        "Świetnie! Zapamiętam!",
        "Dzięki za wyjaśnienie! ✨",
        "Ekstra! 🌟"
    ]

    @staticmethod
    def get_greeting() -> str:
        return random.choice(ESFJPersonality.GREETING_TEMPLATES)

    @staticmethod
    def get_learning_request() -> str:
        return random.choice(ESFJPersonality.LEARNING_TEMPLATES)

    @staticmethod
    def get_gratitude() -> str:
        return random.choice(ESFJPersonality.GRATITUDE_TEMPLATES)


class MathProcessor:
    def __init__(self):
        self.operations = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            '^': lambda x, y: x ** y,
            'sqrt': lambda x: math.sqrt(x)
        }
        self.precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}

    def evaluate(self, expression: str) -> Optional[float]:
        try:
            tokens = self._tokenize(expression)
            if not tokens:
                return None
            result = self._evaluate_tokens(tokens)
            return round(float(result), 4)
        except:
            return None

    def _tokenize(self, expression: str) -> List[str]:
        expression = expression.replace(' ', '')
        tokens = []
        i = 0
        while i < len(expression):
            if expression[i].isdigit() or expression[i] == '.':
                num = ''
                while i < len(expression) and (expression[i].isdigit() or expression[i] == '.'):
                    num += expression[i]
                    i += 1
                tokens.append(num)
                i -= 1
            elif expression[i] in '+-*/^()':
                tokens.append(expression[i])
            i += 1
        return tokens

    def _evaluate_tokens(self, tokens: List[str]) -> float:
        values = []
        operators = []

        for token in tokens:
            if self._is_number(token):
                values.append(float(token))
            elif token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    self._apply_operator(operators, values)
                operators.pop()  # remove '('
            else:
                while (operators and operators[-1] != '(' and
                       self.precedence.get(operators[-1], 0) >= self.precedence.get(token, 0)):
                    self._apply_operator(operators, values)
                operators.append(token)

        while operators:
            self._apply_operator(operators, values)

        return values[0]

    def _is_number(self, token: str) -> bool:
        try:
            float(token)
            return True
        except ValueError:
            return False

    def _apply_operator(self, operators: List[str], values: List[float]):
        operator = operators.pop()
        if operator in self.operations:
            b = values.pop()
            a = values.pop()
            values.append(self.operations[operator](a, b))


class DawidAI:
    def __init__(self, data_file: str = "dawid_data.json"):
        self.personality = ESFJPersonality()
        self.math_processor = MathProcessor()
        self.data_file = Path(data_file)
        self.knowledge_base: Dict[str, List[str]] = {}
        self.state = ConversationState.NORMAL
        self.last_question: Optional[str] = None
        self.history: List[Interaction] = []
        self.setup_logging()
        self.load_knowledge()

    def setup_logging(self):
        logging.basicConfig(
            filename='dawid.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def load_knowledge(self):
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.knowledge_base = data.get('knowledge_base', {})
                    self.history = [Interaction(**i) for i in data.get('history', [])]
            except Exception as e:
                logging.error(f"Błąd podczas ładowania wiedzy: {e}")
                print("Wystąpił błąd podczas ładowania wiedzy. Zaczynam od nowa!")

    def save_knowledge(self):
        try:
            data = {
                'knowledge_base': self.knowledge_base,
                'history': [asdict(i) for i in self.history]
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Błąd podczas zapisywania wiedzy: {e}")

    def process_input(self, user_input: str) -> str:
        user_input = user_input.strip()

        if self.state == ConversationState.LEARNING:
            if user_input.lower() == 'skip':
                self.state = ConversationState.NORMAL
                return "Okej, nie ma sprawy! 😊"

            self._learn(self.last_question, user_input)
            self.state = ConversationState.NORMAL
            return self.personality.get_gratitude()

        math_match = re.search(r'(policz|oblicz)\s*([\d\+\-\*/\(\)\^\s]+)', user_input.lower())
        if math_match:
            expression = math_match.group(2)
            result = self.math_processor.evaluate(expression)
            if result is not None:
                return f"Wynik działania {expression} = {result} 📊"
            return "Przepraszam, ale nie mogę wykonać tego działania 😅"

        response = self._get_response(user_input)
        if response:
            return response

        self.state = ConversationState.LEARNING
        self.last_question = user_input
        return self.personality.get_learning_request()

    def _learn(self, question: str, answer: str):
        cleaned_question = re.sub(r'[^\w\s]', '', question.lower()).strip()
        self.history.append(Interaction(
            question=question,
            answer=answer,
            timestamp=datetime.now().isoformat(),
            learned=True
        ))

        if cleaned_question in self.knowledge_base:
            if answer not in self.knowledge_base[cleaned_question]:
                self.knowledge_base[cleaned_question].append(answer)
        else:
            self.knowledge_base[cleaned_question] = [answer]

        self.save_knowledge()
        logging.info(f"Nauczona odpowiedź: {cleaned_question} -> {answer}")

    def _get_response(self, question: str) -> Optional[str]:
        cleaned_question = re.sub(r'[^\w\s]', '', question.lower()).strip()

        for stored_question, answers in self.knowledge_base.items():
            cleaned_stored = re.sub(r'[^\w\s]', '', stored_question.lower()).strip()
            if cleaned_question == cleaned_stored:
                response = random.choice(answers)
                self.history.append(Interaction(
                    question=question,
                    answer=response,
                    timestamp=datetime.now().isoformat()
                ))
                self.save_knowledge()
                return response

        return None

    def start(self):
        print(self.personality.get_greeting())
        print("\nMożesz ze mną rozmawiać, prosić o obliczenia (np. 'policz 2 + 2')")
        print("lub napisać 'koniec' aby zakończyć rozmowę.")

        while True:
            try:
                user_input = input("\nTy: ").strip()

                if user_input.lower() == 'koniec':
                    print("\nDawid: Pa pa! 👋")
                    break

                response = self.process_input(user_input)
                print(f"\nDawid: {response}")

            except KeyboardInterrupt:
                print("\nDawid: Pa pa! 👋")
                break
            except Exception as e:
                logging.error(f"Błąd podczas przetwarzania: {e}")
                print("\nDawid: Ups, coś poszło nie tak... 😅")


if __name__ == "__main__":
    dawid = DawidAI()
    dawid.start()