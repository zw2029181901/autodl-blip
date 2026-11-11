import functools
from runtime.common import device, guarded, image_rgb, model_path, output_path, page_header


@functools.lru_cache(maxsize=1)
def model_and_processor():
    from transformers import BlipForConditionalGeneration, BlipProcessor
    directory = model_path()
    return BlipForConditionalGeneration.from_pretrained(directory).to(device()).eval(), BlipProcessor.from_pretrained(directory)


@guarded
def caption(image, prefix):
    import torch
    image = image_rgb(image)
    model, processor = model_and_processor()
    kwargs = {"images": image, "return_tensors": "pt"}
    if prefix.strip():
        kwargs["text"] = prefix.strip()[:200]
    inputs = processor(**kwargs).to(device())
    with torch.inference_mode():
        tokens = model.generate(**inputs, max_new_tokens=80, num_beams=3)
    result = processor.decode(tokens[0], skip_special_tokens=True)
    destination = output_path(".txt")
    destination.write_text(result, encoding="utf-8")
    return result, str(destination)


def build_ui():
    import gradio as gr
    with gr.Blocks(title="BLIP 看图描述") as ui:
        page_header()
        gr.Markdown("输出英文画面描述，可作为图片索引或出图提示词的起点。")
        image = gr.Image(type="pil", label="图片")
        prefix = gr.Textbox(label="可选英文开头", placeholder="a photograph of")
        button = gr.Button("生成描述", variant="primary")
        result = gr.Textbox(label="英文描述", lines=5)
        file = gr.File(label="下载 TXT")
        button.click(caption, [image, prefix], [result, file], api_name="caption")
    return ui
