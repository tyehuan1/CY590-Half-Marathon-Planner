import gradio as gr
import os

from cy590_half_marathon_planner.coach import MAX_INPUT_CHARS, respond
from cy590_half_marathon_planner.pdf_export import export_plan_pdf
from cy590_half_marathon_planner.intake import (
    CROSS_TRAINING,
    CROSS_TRAINING_SLOTS,
    DAYS,
    DEVICES,
    EXPERIENCE,
    RACE_DISTANCES,
    SURFACES,
    TEMPERATURES,
    build_intake_message,
    validate,
)

DESCRIPTION = (
    "Fill in the intake form and generate a plan. Use the follow-up box "
    "underneath to ask questions or adjust anything afterward."
)


def stream_into_chat(message: str, history: list[dict]):
    """Append a user message and stream the assistant reply into the chatbot."""
    history = list(history or [])
    prior = list(history)
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": ""})
    yield list(history), ""

    for partial in respond(message, prior):
        history[-1] = {"role": "assistant", "content": partial}
        yield list(history), ""


def on_generate(*values):
    """Validate the form, then build and send the intake message."""
    (
        surface, weeks, goal_h, goal_m, goal_s, mileage, experience,
        injuries, goals, long_run_day, race_surface, elevation,
        days_unavailable, longest_run, race_distance,
        race_h, race_m, race_s, age, temperature, device, history,
    ) = values[:22]
    cross_values = values[22:]

    errors = validate(
        weeks, goal_h, goal_m, goal_s, mileage, long_run_day,
        days_unavailable, longest_run, race_distance,
        race_h, race_m, race_s, cross_values,
    )
    if errors:
        raise gr.Error("Please fix the following:\n" + "\n".join(f"- {e}" for e in errors))

    message = build_intake_message(
        surface, cross_values, weeks, goal_h, goal_m, goal_s, mileage,
        experience, injuries, goals, long_run_day, race_surface, elevation,
        days_unavailable, longest_run, race_distance, race_h, race_m, race_s,
        age, temperature, device,
    )
    yield from stream_into_chat(message, history)

def on_export_pdf(history: list[dict]):
    try:
        return export_plan_pdf(history)
    except ValueError as e:
        raise gr.Error(str(e))

def build_demo() -> gr.Blocks:
    with gr.Blocks(
        title="Half-Marathon Training Plan Builder",
        analytics_enabled=False,
    ) as demo:
        gr.Markdown("# Half-Marathon Training Plan Builder")
        gr.Markdown(DESCRIPTION)

        with gr.Row():
            # ---------------- Intake form ----------------
            with gr.Column(scale=1):
                with gr.Accordion("About the race", open=True):
                    weeks = gr.Slider(1, 20, value=12, step=1,
                                      label="Weeks until the half marathon")
                    with gr.Row():
                        goal_h = gr.Number(value=2, minimum=0, maximum=5,
                                           step=1, label="Goal hours")
                        goal_m = gr.Number(value=0, minimum=0, maximum=59,
                                           step=1, label="Minutes")
                        goal_s = gr.Number(value=0, minimum=0, maximum=59,
                                           step=1, label="Seconds")
                    race_surface = gr.Dropdown(SURFACES, value="Road",
                                               label="Race-day surface")
                    elevation = gr.Slider(0, 2500, value=0, step=25,
                                          label="Race elevation gain (feet)")

                with gr.Accordion("About you", open=True):
                    age = gr.Slider(16, 99, value=30, step=1, label="Age")
                    experience = gr.Dropdown(EXPERIENCE, value="Intermediate",
                                             label="Level of experience")
                    mileage = gr.Slider(1, 80, value=15, step=1,
                                        label="Current weekly mileage (miles)")
                    longest_run = gr.Slider(1, 50, value=6, step=1,
                                            label="Longest run in the past month (miles)")
                    race_distance = gr.Dropdown(RACE_DISTANCES,
                                                value="No recent race",
                                                label="Recent race or time trial")
                    with gr.Row():
                        race_h = gr.Number(value=0, minimum=0, maximum=5,
                                           step=1, label="Hours")
                        race_m = gr.Number(value=0, minimum=0, maximum=59,
                                           step=1, label="Minutes")
                        race_s = gr.Number(value=0, minimum=0, maximum=59,
                                           step=1, label="Seconds")

                with gr.Accordion("Your schedule", open=True):
                    long_run_day = gr.Dropdown(DAYS, value="Saturday",
                                               label="Preferred long-run day")
                    days_unavailable = gr.CheckboxGroup(DAYS, value=[],
                                                label="Days you cannot train (no running or cross-training)")
                    surface = gr.Dropdown(SURFACES, value="Road",
                                                label="Preferred training surface")
                    temperature = gr.Dropdown(TEMPERATURES, value="Mild (55-69F)",
                                                label="Training temperature")
                    device = gr.Dropdown(DEVICES, value="GPS watch",
                                                label="Training device")

                with gr.Accordion("Cross-training", open=False):
                    gr.Markdown("Leave a row set to *None* to skip it.")
                    cross_components = []
                    for i in range(CROSS_TRAINING_SLOTS):
                        with gr.Row():
                            ct_type = gr.Dropdown(
                                CROSS_TRAINING, value="None",
                                label=f"Type {i + 1}", scale=2)
                            ct_days = gr.Slider(
                                0, 7, value=0, step=1,
                                label="Days/week", scale=1)
                        cross_components.extend([ct_type, ct_days])

                with gr.Accordion("Notes", open=False):
                    injuries = gr.Textbox(
                        label="Injuries or health concerns (current or historical)",
                        lines=3, max_length=500,
                        placeholder="e.g. recurring IT band pain in the left knee")
                    goals = gr.Textbox(
                        label="Specific goals or preferences",
                        lines=3, max_length=500,
                        placeholder="e.g. I'd like to avoid track workouts")

                generate_btn = gr.Button("Generate my plan", variant="primary")

            # ---------------- Chat output ----------------
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    height=800,
                    resizable=True,
                    allow_tags=False,
                    label="Training Plan",
                )
                followup = gr.Textbox(
                    label="Follow-up",
                    placeholder="Ask a question or request a change...",
                    max_length=MAX_INPUT_CHARS,
                )
                with gr.Row():
                    clear_btn = gr.ClearButton([chatbot, followup], value="Clear")
                    pdf_btn = gr.DownloadButton(
                        "Download PDF (landscape)", variant="secondary")

        form_inputs = [
            surface, weeks, goal_h, goal_m, goal_s, mileage, experience,
            injuries, goals, long_run_day, race_surface, elevation,
            days_unavailable, longest_run, race_distance,
            race_h, race_m, race_s, age, temperature, device, chatbot,
        ] + cross_components

        generate_btn.click(
            fn=on_generate,
            inputs=form_inputs,
            outputs=[chatbot, followup],
            api_name="generate_plan",
            api_visibility="private",
        )

        followup.submit(
            fn=stream_into_chat,
            inputs=[followup, chatbot],
            outputs=[chatbot, followup],
            api_name="followup",
            api_visibility="private",
        )

        pdf_btn.click(
            fn=on_export_pdf,
            inputs=[chatbot],
            outputs=[pdf_btn],
            api_name="export_pdf",
            api_visibility="private",
        )

        clear_btn.click(lambda: None, api_visibility="private")

    return demo


def main() -> None:
    demo = build_demo()
    demo.queue(default_concurrency_limit=2, max_size=20)
    demo.launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
        share=False,
        footer_links=["gradio", "settings"],
    )


if __name__ == "__main__":
    main()