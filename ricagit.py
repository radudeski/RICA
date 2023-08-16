import os
import json
import openai
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import speech_recognition as sr
import pyttsx3
import multiprocessing

conversations = {}

# Replace with your actual API key
openai.api_key = "YOUR API HERE"
openai_api_url = "https://api.openai.com/v1/engines/davinci-codex/completions"

def create_gui():
    root = tk.Tk()
    
    root.title("RICA - Resource Intelligence Collaborative Assistant")
    root.geometry("800x600")
    
    popup_menu = tk.Menu(root, tearoff=0)
    popup_menu.add_command(label="Rename", command=rename_chat)
    popup_menu.add_command(label="Delete", command=delete_chat)

    style = ttk.Style()
    style.theme_use('xpnative')

    # Create a frame for the entire interface with a margin
    main_frame = ttk.Frame(root, padding="10 10 10 10")
    main_frame.pack(fill=tk.BOTH, expand=True)
    # Set the background color for the main frame
    

    # Create a frame for the chat list
    chat_list_frame = ttk.Frame(main_frame)
    chat_list_frame.pack(side=tk.LEFT, fill=tk.Y)
    
    chat_list_button_frame = ttk.Frame(chat_list_frame)
    chat_list_button_frame.pack(side=tk.TOP, fill=tk.X)

    chat_list = tk.Listbox(chat_list_frame)
    chat_list.pack(side=tk.LEFT, fill=tk.Y)
    chat_list.bind("<Button-3>", on_right_click)  # Right-click event


    new_chat_button = tk.Button(chat_list_button_frame, text="New Chat", command=lambda: create_new_chat(chat_list))
    new_chat_button.pack(side=tk.TOP, fill=tk.X) # Make it wider by filling the X dimension
    new_chat_button.configure(bg='grey', fg='black', activebackground='grey', activeforeground='white')

        # Create a frame for RICA's terminal responses
    rica_terminal_frame = ttk.Frame(main_frame)
    rica_terminal_frame.pack(side=tk.TOP, fill=tk.X)
    
    rica_terminal_window = tk.Text(rica_terminal_frame, width=60, height=8) # 25% height of the chat window
    rica_terminal_window.pack(side=tk.TOP, fill=tk.X, expand=True)
    #rica_terminal_window.configure(bg='black', fg='white', insertbackground='white')
    
    # Create a frame for the chat window and input bar
    chat_frame = ttk.Frame(main_frame)
    chat_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    chat_window = tk.Text(chat_frame, width=60, height=22) # Adjust the height as needed
    chat_window.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    #chat_window.configure(bg='black', fg='white', insertbackground='white')
   

    # Create a frame for the input bar and send button
    input_frame = ttk.Frame(chat_frame)
    input_frame.pack(side=tk.BOTTOM, fill=tk.X)

    input_bar = tk.Entry(input_frame, width=80)  # Set the width as needed
    input_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)  # Place it to the left within the frame
    #input_bar.configure(bg='black', fg='white', insertbackground='white')
    
    voice_input_toggle = tk.BooleanVar(value=False)
    voice_input_checkbox = tk.Checkbutton(root, text="Voice Input", variable=voice_input_toggle)
    voice_input_checkbox.pack(side=tk.LEFT, fill=tk.X)
    #voice_input_checkbox.configure(bg='black', fg='white')

    voice_output_toggle = tk.BooleanVar(value=False)
    voice_output_checkbox = tk.Checkbutton(root, text="Voice Output", variable=voice_output_toggle)
    voice_output_checkbox.pack(side=tk.LEFT, fill=tk.X)
    #voice_output_checkbox.configure(bg='black', fg='white')

    # Use a lambda to pass the required arguments to send_message
    send_button = tk.Button(input_frame, text="Send", 
    command=lambda: send_message(get_current_chat_name(), input_bar, voice_input_toggle, voice_output_toggle, chat_window, rica_terminal_window))
    send_button.pack(side=tk.RIGHT)
    send_button.configure(bg='grey', fg='black', activebackground='grey', activeforeground='white')

    
    # Bind the Enter key to send messages
    input_bar.bind('<Return>', lambda event: send_message(get_current_chat_name(chat_list), input_bar, voice_input_toggle, voice_output_toggle, chat_window, rica_terminal_window))


    # Bind the Escape key to exit the program
    root.bind('<Escape>', lambda event: root.quit())
    
    chat_list.bind("<ButtonRelease-1>", lambda event: on_chat_select(event, chat_list, chat_window))
    
    root.mainloop()


def get_gpt4_response(conversation):
    try:
        prompt = "\n".join(conversation)  # Combine the conversation into a single string
        print("Generating...", prompt)  # Print the prompt for debugging
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=json.dumps(prompt),  # Convert the conversation to a JSON string
            max_tokens=200,
            temperature=0.4,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def load_chat_conversation(chat_name):
    chat_directory = "chats"
    chat_file_path = os.path.join(chat_directory, f"{chat_name}.txt")

    if not os.path.exists(chat_directory):
        create_directory = input(f"The directory '{chat_directory}' does not exist. Would you like to create it? (y/n): ").lower()

        if create_directory == 'y':
            os.makedirs(chat_directory)
            print(f"Directory '{chat_directory}' created.")
        else:
            print(f"Directory '{chat_directory}' was not created.")
    else:
        print(f"Directory '{chat_directory}' already exists.")

        if os.path.exists(chat_file_path): # Check if chat file exists
            # Read the chat conversation from the file
            with open(chat_file_path, 'r') as chat_file:
                conversation = chat_file.read()
            
            return conversation
        
        # Check and create the chat file if it doesn't exist
    if not os.path.exists(chat_file_path):
        with open(chat_file_path, 'w') as chat_file:
            print(f"Chat file '{chat_file_path}' created.")
            return "" # Return an empty string since the file is new
    
   
    
def get_voice_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for 'RICA'...")
        while True:
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio)
                if 'RICA' in text:
                    print("How may I help?")
                    # Further processing here
            except:
                pass

def create_new_chat(chat_list):
    chat_name = simpledialog.askstring("Chat Name", "Enter the name for the new chat:")
    if chat_name:
        chat_list.insert(tk.END, chat_name)


def delete_chat(event):
    selected_index = chat_list.curselection()[0]
    selected_chat = chat_list.get(selected_index)
    answer = messagebox.askokcancel("Delete Chat", f"Are you sure you want to delete '{selected_chat}'?")
    if answer:
        chat_list.delete(selected_index)
        # Add more logic to delete the chat from your data structure

def rename_chat(event):
    selected_index = chat_list.curselection()[0]
    new_name = simpledialog.askstring("Rename Chat", "Enter new chat name:")
    chat_list.delete(selected_index)
    chat_list.insert(selected_index, new_name)
    # Add more logic to rename the chat in your data structure

def on_right_click(event):
    popup_menu.post(event.x_root, event.y_root)

def on_chat_select(event, chat_list, chat_window):
    selected_index = chat_list.curselection()
    if selected_index:
        selected_chat = chat_list.get(selected_index[0])
        conversation = load_chat_conversation(selected_chat)
        chat_window.delete(1.0, tk.END)  # Clear the chat window
        chat_window.insert(tk.END, conversation)  # Insert the loaded conversation

def get_current_chat_name(chat_list):
    selected_index = chat_list.curselection()
    if selected_index:
        return chat_list.get(selected_index[0])
    return None
    
def send_message(chat_name, input_bar, voice_input_toggle, voice_output_toggle, chat_window, rica_terminal_window):
    user_input = input_bar.get()
    input_bar.delete(0, tk.END)  # Clear the input bar
    user_message = f"User: {user_input}\n" # Prepare user input
    rica_terminal_window.insert(tk.END, user_message)  # Send user input to RICA's terminal
    process_rica_response(user_input, voice_input_toggle, voice_output_toggle, chat_window, rica_terminal_window) # Process RICA's response
    if voice_input_toggle.get():
        multiprocessing.Process(target=get_voice_input).start()
    conversation = conversations.get(chat_name, [])
    conversation.append(f"User: {user_input}")
    conversation.append(f"RICA: {get_gpt4_response(conversation)}")
    conversations[chat_name] = conversation
    update_chat_conversation(chat_name, user_message + rica_response)

def process_rica_response(user_input, voice_input_toggle, voice_output_toggle, chat_window, rica_terminal_window):
    response = get_gpt4_response(user_input) # Get GPT-4's response
    rica_response = f"RICA: {response}\n"
    rica_terminal_window.insert(tk.END, rica_response) # Insert into RICA terminal window
    chat_window.insert(tk.END, rica_response) # Add RICA's response to the main chat window
    if voice_output_toggle.get():
        send_voice_response(response)



# Function to send a voice response
def send_voice_response(response):
    engine = pyttsx3.init()
    engine.say(response)
    engine.runAndWait()



if __name__ == "__main__":
    create_gui()
