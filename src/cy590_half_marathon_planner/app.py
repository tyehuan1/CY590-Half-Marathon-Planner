import gradio as gr

from cy590_half_marathon_planner.coach import MAX_INPUT_CHARS, respond

DESCRIPTION = (
    "Describe your running background and goal race and I'll build a "
    "personalized plan. The more of the intake questions you answer, "
    "the more tailored the plan will be."
)

EXAMPLES = [
    "I'm running a half marathon in 12 weeks. Currently 15 miles/week over "
    "4 days, longest recent run 7 miles, goal time 2:00. Road race with "
    "500 ft of gain. No injuries. I'd like long runs on Saturday.",
    "Complete beginner, 20 weeks out, I can run 2 miles right now. "
    "I just want to finish.",
    "What information do you need from me?",
]


def build_demo() -> gr.ChatInterface:
    chatbot = gr.Chatbot(
        height=650,
        resizable=True,
        allow_tags=False,
        label="Training Plan",
    )
    textbox = gr.Textbox(
        placeholder="Describe your goal race, current mileage, and schedule...",
        max_length=MAX_INPUT_CHARS,
    )
    return gr.ChatInterface(
        fn=respond,
        chatbot=chatbot,
        textbox=textbox,
        title="Half-Marathon Training Plan Builder",
        description=DESCRIPTION,
        examples=EXAMPLES,
        cache_examples=False,
        save_history=True,
    )


def main() -> None:
    demo = build_demo()
    demo.queue(default_concurrency_limit=2, max_size=20)
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_api=False,
    )


if __name__ == "__main__":
    main()