MAX_HISTORY = 5

conversation_history = []

def add_message(role :str , content : str):
    conversation_history.append({"role": role, "content": content})
    
    if len(conversation_history) > MAX_HISTORY:
        conversation_history.pop(0)
        
def get_history():
    return conversation_history