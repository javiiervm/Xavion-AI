from chatbot.keywords import (
    INSTRUCTION_MAP,
    STOPWORDS, 
    DEFINITION_KEY_WORDS,
    TEACHING_PATTERNS,
    MATH_PATTERNS,
    SAFE_MATH_FUNCS,
    GREETING_KEYWORDS,
    THANKS_KEYWORDS
)
from chatbot.utils import (
    extract_math_expression,
    evaluate_math_expression,
    extract_keywords,
    extract_teaching,
    delete_stopwords
)
import re
import json

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"

class Command:
    __slots__ = ('intent', 'instruction', 'knowledge')

    def __init__(self):
        self.intent = ''
        self.instruction = ''
        self.knowledge = ''

    def set_intent(self, intent):
        self.intent = ''
        self.intent = intent

    def set_instruction(self, instruction):
        self.instruction = ''
        self.instruction = instruction
    
    def set_knowledge(self, knowledge):
        self.knowledge = ''
        self.knowledge = knowledge

    def get_intent(self):
        return self.intent

    def get_instruction(self):
        return self.instruction

    def get_knowledge(self):
        return self.knowledge

    def build_instruction(self, debug_mode):
        self.instruction = ''
        if self.intent == "greeting":
            if "to " in self.instruction.lower() or "a " in self.instruction.lower():
                self.instruction = 'Instruction: Say hello to the person the user mentioned. Use their name if possible. Do not define what greetings are.'
            else:
                self.instruction = 'Instruction: ' + INSTRUCTION_MAP["greeting"]
        else:
            self.instruction = 'Instruction: ' + INSTRUCTION_MAP.get(self.intent, "reply naturally and continue the topic, always end with a question.")
        if debug_mode:
                print(f"{BOLD}📝 Instruction: {GREEN}{self.instruction}{RESET}")

    def build_chatbot_command(self, user_input, KNOWLEDGE_DB, USER_MEMORY, MEMORY_PATH, debug_mode):
        self.set_intent(self.detect_intent(user_input, debug_mode, USER_MEMORY, MEMORY_PATH))
        if debug_mode:
            print(f"{BOLD}🔎 Confirmed intent: {GREEN}{self.intent}{RESET}")
        if self.intent in ["definition"]:
            self.set_knowledge(self.search_for_knowledge(extract_keywords(user_input), KNOWLEDGE_DB, USER_MEMORY, debug_mode))
        self.build_instruction(debug_mode)
        if debug_mode:
            print(f"{BOLD}📝 FINAL SUMMARY:\nIntent: {self.intent}\nInstruction: {self.instruction}\nKnowledge: {self.knowledge}{RESET}")

    def search_for_knowledge(self, keywords, KNOWLEDGE_DB, USER_MEMORY, debug_mode):
        knowledge = ''
        if keywords:
            if debug_mode:
                print(f"{BOLD}🔎 Keywords detected: {GREEN}{keywords}{RESET}")
            for keyword in keywords:
                if keyword in KNOWLEDGE_DB:
                    if debug_mode:
                        print(f"🔎 Keyword '{keyword}': {KNOWLEDGE_DB[keyword]["knowledge"]}.{RESET}")
                    knowledge += KNOWLEDGE_DB[keyword]["knowledge"] + "\n"
                elif keyword in USER_MEMORY:
                    if debug_mode:
                        print(f"🔎 Keyword '{keyword}': {USER_MEMORY[keyword]["knowledge"]}.{RESET}")
                    knowledge += USER_MEMORY[keyword]["knowledge"] + "\n"
                else:
                    if debug_mode:
                        print(f"{BOLD}⚠️ Keyword '{keyword}' not found in knowledge base.{RESET}")
        else:
            if debug_mode:
                print(f"{BOLD}⚠️ No keywords detected in user input.{RESET}")
        return knowledge

    def detect_intent(self, user_input, debug_mode, USER_MEMORY, MEMORY_PATH):
        """
        Detects the intent of the user's input.

        Args:
            user_input (str): The user's input.

        Returns:
            str: The detected intent
        """
        text = user_input.lower().strip()

        # Check for greeting
        if any(greet in text for greet in GREETING_KEYWORDS):
            if self.double_check_intent(user_input, "greeting", debug_mode, USER_MEMORY, MEMORY_PATH):
                return "greeting"
            else:
                if debug_mode:
                    print(f"{BOLD}❌ Rejected greeting intent.{RESET}")

        # Check for thanks
        if any(thank in text for thank in THANKS_KEYWORDS):
            if self.double_check_intent(user_input, "thanks", debug_mode, USER_MEMORY, MEMORY_PATH):
                return "thanks"
            else:
                if debug_mode:
                    print(f"{BOLD}❌ Rejected thanks intent.{RESET}")

        # Check for math
        for pattern in MATH_PATTERNS:
            if re.search(pattern, text):
                if self.double_check_intent(user_input, "math", debug_mode, USER_MEMORY, MEMORY_PATH):
                    return "math"
        if debug_mode:
            print(f"{BOLD}❌ Rejected math intent.{RESET}")

        # Check for definition
        if any(keyword in text for keyword in DEFINITION_KEY_WORDS):
            if self.double_check_intent(user_input, "definition", debug_mode, USER_MEMORY, MEMORY_PATH):

                return "definition"
            else:
                if debug_mode:
                    print(f"{BOLD}❌ Rejected definition intent.{RESET}")

        # Add non-definition question here

        # Check for teaching
        for pattern in TEACHING_PATTERNS:
            if re.search(pattern, text):
                if self.double_check_intent(user_input, "teaching", debug_mode, USER_MEMORY, MEMORY_PATH):

                    return "teaching"
                else:
                    if debug_mode:
                        print(f"{BOLD}❌ Rejected teaching intent.{RESET}")

        # Default: conversation
        return "conversation"

    def double_check_intent(self, user_input, intent, debug_mode, USER_MEMORY, MEMORY_PATH):
        if debug_mode:
            print(f"🔎 Double-checking intent: {intent}")

        if intent == "greeting" or intent == "thanks":
            return True

        if intent == "math":
            expression = extract_math_expression(user_input, debug_mode)
            if debug_mode:
                print(f"{BOLD}🔎 Expression detected: {GREEN}{expression}{RESET}")
            if expression:
                result = evaluate_math_expression(expression, debug_mode)
                if debug_mode:
                    print(f"{BOLD}🔎 Result: {GREEN}{result}{RESET}")
                self.set_knowledge(f"The result of the expression '{expression}' is {result}.")
                return True
            else:
                if debug_mode:
                    print(f"{BOLD}⚠️ No math expression detected in user input. Reconsidering...{RESET}")

        if intent == "definition":
            return True

        if intent == "teaching":
                # Add to memory new things learnt
                term, definition = extract_teaching(user_input)
                if term and definition:
                    term = delete_stopwords(term)
                    USER_MEMORY[term] = {"knowledge": definition}
                    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
                        json.dump(USER_MEMORY, f, ensure_ascii=False, indent=2)
                    if not debug_mode:
                        print("")
                    print(f"{BOLD}✅ New knowledge added to memory: {GREEN}{term}{RESET}")
                    print(f"{BOLD}{GREEN}💡 '{term}' means '{definition}'{RESET}")
                    return True
                else:
                    if debug_mode:
                        print(f"{BOLD}⚠️ No teaching pattern detected in user input. Reconsidering...{RESET}")

        return False