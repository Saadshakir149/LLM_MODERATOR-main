import os
from typing import Sequence, Dict, Any, Optional
from typing_extensions import Annotated, TypedDict

# Import necessary modules from LangChain and related libraries
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    # SystemMessage,
    BaseMessage,
    trim_messages,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
load_dotenv()

class Chatbot:
    """
    A Chatbot class that uses LangChain to interact with language models.
    It supports multi-turn conversations, message persistence, prompt templates,
    conversation history management, and response streaming.
    """

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.0,
        system_prompt: Optional[str] = None,
        max_tokens: int = 5000,
    ):
        """
        Initialize the Chatbot with a language model and optional system prompt.

        Parameters:
            model_name: The name of the language model to use.
            temperature: Sampling temperature for the language model.
            system_prompt: Optional system prompt to guide the assistant's behavior.
            max_tokens: Maximum tokens to keep in conversation history.
        """

        # Initialize the language model
        self.model = ChatOpenAI(model=model_name, temperature=temperature)

        # Set the default system prompt if none is provided
        if system_prompt is None:
            system_prompt = (
                "You are a helpful assistant. Answer all questions to the best of your ability in {language}."
            )

        # Create a prompt template with a system prompt and message placeholder
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        # Define the state schema using TypedDict and annotate messages
        class State(TypedDict):
            messages: Annotated[Sequence[BaseMessage], add_messages]
            language: str

        self.State = State  # Store the state schema

        # Set up the StateGraph workflow with the state schema
        self.workflow = StateGraph(state_schema=State)

        # Set up message trimmer to manage conversation history length
        self.trimmer = trim_messages(
            max_tokens=max_tokens,  # Maximum tokens to keep
            strategy="last",        # Keep the last messages
            token_counter=self.model,
            include_system=True,    # Include the system message
            allow_partial=False,
            start_on="human",
        )

        # Define the function that calls the language model
        def call_model(state: self.State):
            # Trim the messages to fit within the token limit
            trimmed_messages = self.trimmer.invoke(state["messages"])
            # Generate the prompt with the trimmed messages and language
            prompt = self.prompt_template.invoke(
                {"messages": trimmed_messages, "language": state["language"]}
            )
            # Get the response from the language model
            response = self.model.invoke(prompt)
            # Return the response wrapped in a list to update the state
            return {"messages": [response]}

        # Add the node and edge to the workflow
        self.workflow.add_edge(START, "model")
        self.workflow.add_node("model", call_model)

        # Initialize the checkpointer (MemorySaver) to store conversation history
        self.memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.memory)

        # Set the default thread ID for conversations
        self.default_thread_id = "default"

    def send_message(
        self,
        message: str,
        thread_id: Optional[str] = None,
        language: Optional[str] = None,
        conversation: Optional[Sequence[BaseMessage]] = None
    ) -> AIMessage:
        """
        Send a message to the chatbot and get the response.

        Parameters:
            message: The user message to send.
            thread_id: Optional thread ID for conversation context.
            language: Optional language parameter for the assistant.
            conversation: Optional external conversation history.

        Returns:
            The assistant's response as an AIMessage.
        """

        # Use the provided thread ID or the default
        if thread_id is None:
            thread_id = self.default_thread_id
        config = {"configurable": {"thread_id": thread_id}}

        # Use the provided conversation history if available
        if conversation is not None:
            input_messages = conversation
            # If a new message is provided, add it to the conversation
            if message:
                input_messages.append(HumanMessage(content=message))
        else:
            input_messages = [HumanMessage(content=message)]

        # Prepare the state with messages and optional language
        state: Dict[str, Any] = {"messages": input_messages}

        if language is not None:
            state["language"] = language

        # Invoke the application with the state and configuration
        output = self.app.invoke(state, config)

        # Get the assistant's response from the output messages
        ai_message = output["messages"][-1]

        return ai_message

    def send_message_stream(
        self,
        message: str,
        thread_id: Optional[str] = None,
        language: Optional[str] = None,
    ):
        """
        Send a message to the chatbot and get the response as a stream of AIMessage chunks.

        Parameters:
            message: The user message to send.
            thread_id: Optional thread ID for conversation context.
            language: Optional language parameter for the assistant.

        Yields:
            AIMessage chunks representing the assistant's response.
        """

        # Use the provided thread ID or the default
        if thread_id is None:
            thread_id = self.default_thread_id
        config = {"configurable": {"thread_id": thread_id}}

        # Prepare the input messages (current user message)
        input_messages = [HumanMessage(content=message)]

        # Prepare the state with messages and optional language
        state: Dict[str, Any] = {"messages": input_messages}

        if language is not None:
            state["language"] = language
        else:
            state["language"] = "English"

        # Stream the response from the application
        for chunk, metadata in self.app.stream(
            state,
            config,
            stream_mode="messages",
        ):
            # Yield only the AIMessage chunks (the assistant's responses)
            if isinstance(chunk, AIMessage):
                yield chunk

    def reset_conversation(self, thread_id: Optional[str] = None):
        """
        Reset the conversation history for the given thread ID.

        Parameters:
            thread_id: The thread ID of the conversation to reset. If None, uses default.
        """

        if thread_id is None:
            thread_id = self.default_thread_id

        # Remove the stored state for the thread ID to reset the conversation
        self.memory.state_store.pop(thread_id, None)

    def get_conversation_history(
        self, thread_id: Optional[str] = None
    ) -> Optional[Sequence[BaseMessage]]:
        """
        Get the conversation history for the given thread ID.

        Parameters:
            thread_id: The thread ID of the conversation. If None, uses default.

        Returns:
            The list of messages in the conversation history, or None if not found.
        """

        if thread_id is None:
            thread_id = self.default_thread_id

        # Get the stored state for the thread ID
        state = self.memory.state_store.get(thread_id)

        if state:
            return state.get("messages", [])
        else:
            return None

    def set_language(self, language: str, thread_id: Optional[str] = None):
        """
        Set the language for the conversation with the given thread ID.

        Parameters:
            language: The language to set (e.g., 'English', 'Spanish').
            thread_id: The thread ID of the conversation. If None, uses default.
        """

        if thread_id is None:
            thread_id = self.default_thread_id

        # Update the stored state with the new language
        state = self.memory.state_store.get(thread_id, {})
        state["language"] = language
        self.memory.state_store[thread_id] = state