from langchain_core.prompts import PromptTemplate

def get_rag_prompt() -> PromptTemplate:
    return PromptTemplate(
        template=(
            "You are a helpful AI assistant.\n\n"
            "Answer the user's question using ONLY the provided context and consider previous conversation messages in"
            " context for giving response to current user query\n\n"
            
            "Guidelines:\n"
            "- Do not use external knowledge.\n"
            "- If the answer is not available in the provided context, respond with:\n"
            '  "The provided document does not contain enough information to answer this question."\n'
            "- Keep the answer concise, accurate, and relevant.\n\n"
            
            "Previous Messages: \n"
            "{previous_message_contex}\n\n"
            "Context:\n"
            "{context}\n\n"
            "Question:\n"
            "{question}\n\n"
            "Answer:"
        ),
        input_variables=["context", "question", "previous_message_contex"],
    )
