from chatbot.model import load_model_and_tokenizer
from chatbot.logic import prepare_input, generate_response
from chatbot.utils import detect_greeting_request

def start_chat():
    # Loads model, tokenizer and device (CPU or GPU)
    model, tokenizer, device = load_model_and_tokenizer()

    print("🤖 AI Chatbot (GODEL) started. Write 'exit' to finish.\n")

    # Conversation variables
    knowledge = ""  # External information
    conversation_history = []

    while True:
        user_input = input(">> ").strip()

        if user_input.lower() == "exit":
            print("🤖: Goodbye!\n")
            break

        # Update conversation history
        conversation_history.append(f"User: {user_input}")
        context = " ".join(conversation_history[-3:])   # Last 3 interactions as provided context

        # Prepare structured input
        input_text = prepare_input(
            instruction="act like a friendly assistant and respond appropriately",
            knowledge=knowledge,
            conversation=context
        )

        # Generate reponse
        reponse = generate_response(model, tokenizer, input_text, device)

        # Show reponse and update history
        print("🤖: ", reponse)
        conversation_history.append(f"Bot: {reponse}")

if __name__ == "__main__":
    start_chat()