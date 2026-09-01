import inspect
import gradio as gr

print(gr.__version__)
print(inspect.signature(gr.Blocks.launch))
print(inspect.signature(gr.ChatInterface.__init__))
print(inspect.signature(gr.Chatbot.__init__))