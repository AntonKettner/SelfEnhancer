from openai import OpenAI
import os
from dotenv import load_dotenv
from src.utils import calculate_cost, pretty_print_conversation


class ControllingAgent:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0

    def evaluate_ideas(self, ideas):
        prompt = "Evaluate and rank the following enhancement ideas based on their potential impact and feasibility:\n\n"
        prompt += ideas
        prompt += "\nSort these ideas from most to least important. Example: 1. Idea 1\n\n2. Idea 2\n\n3. Idea 3"

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that evaluates and ranks ideas.",
            },
            {"role": "user", "content": prompt},
        ]

        pretty_print_conversation(messages)

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages, max_tokens=500
        )

        pretty_print_conversation(
            [{"role": "assistant", "content": response.choices[0].message.content}]
        )

        self.total_input_tokens += response.usage.prompt_tokens
        self.total_output_tokens += response.usage.completion_tokens
        self.total_cost += calculate_cost(
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
            "gpt-3.5-turbo",
        )

        evaluation = response.choices[0].message.content
        ranked_ideas = self._parse_best_idea(evaluation)
        return ranked_ideas

    def review_step(self, step, implementation):
        max_loop_count = 5
        loop_count = 0
        review_history = []

        while loop_count < max_loop_count:
            loop_count += 1
            
            system_prompt = f"""
            Review the IMPLEMENTATION of the step: \n{step}\n and provide feedback:
            
            Is this step correct and efficient? If not, suggest improvements.
            If the implementation is SATISFACTORY, ONLY ANSWER 'TRUE'.
            
            This is review iteration {loop_count} of maximum {max_loop_count}.
            
            Previous review history:
            {self._format_review_history(review_history)}
            """

            messages = [
                {"role": "system", "content": f"You are a PROFESSIONAL SOFTWARE ENGINEER that reviews code implementation steps.\n{system_prompt}"},
                {"role": "user", "content": f"IMPLEMENTATION:\n{implementation}"},
            ]

            pretty_print_conversation(messages)

            model_review = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=4096
            )

            review = model_review.choices[0].message.content
            pretty_print_conversation([{"role": "assistant", "content": review}])

            self.total_input_tokens += model_review.usage.prompt_tokens
            self.total_output_tokens += model_review.usage.completion_tokens
            self.total_cost += calculate_cost(model_review.usage.prompt_tokens, model_review.usage.completion_tokens, "gpt-3.5-turbo")

            if review.strip().lower() == 'true':
                print(f"Implementation satisfactory after {loop_count} iterations.")
                return implementation

            review_history.append(review)
            implementation = self._apply_suggestions(implementation, review)

        print(f"Maximum iterations ({max_loop_count}) reached. Returning last implementation.")
        return implementation

    def _parse_best_idea(self, evaluation):
        ranked_ideas = []
        remaining_eval = evaluation

        for i in range(1, 10):  # Assuming we won't have more than 9 ranked ideas
            start = remaining_eval.find(f"{i}.")
            if start == -1:
                break

            next_idea = remaining_eval.find(f"{i+1}.")
            if next_idea == -1:
                idea = remaining_eval[start:].strip()
            else:
                idea = remaining_eval[start:next_idea].strip()

            ranked_ideas.append(idea)
            remaining_eval = remaining_eval[next_idea:]

        return ranked_ideas

    def _parse_review(self, review):
        # Simple parsing logic, can be improved for more robust extraction
        if "not correct" in review.lower() or "not efficient" in review.lower():
            return False, review
        return True, review

    def _apply_suggestions(self, implementation, review):
        prompt = f"""
        Apply the following suggestions to the implementation:
        
        IMPLEMENTATION:
        {implementation}
        
        SUGGESTIONS:
        {review}
        
        Please provide the updated implementation incorporating these suggestions.
        """

        messages = [
            {"role": "system", "content": "You are SENIOR SOFTWARE ENGINEER that applies code improvement suggestions."},
            {"role": "user", "content": prompt},
        ]

        pretty_print_conversation(messages)

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=4096
        )

        updated_implementation = response.choices[0].message.content
        pretty_print_conversation([{"role": "assistant", "content": updated_implementation}])

        self.total_input_tokens += response.usage.prompt_tokens
        self.total_output_tokens += response.usage.completion_tokens
        self.total_cost += calculate_cost(response.usage.prompt_tokens, response.usage.completion_tokens, "gpt-3.5-turbo")

        return updated_implementation

    def _format_review_history(self, review_history):
        if not review_history:
            return "No previous reviews."
        return "\n\n".join([f"Review {i+1}:\n{review}" for i, review in enumerate(review_history)])
