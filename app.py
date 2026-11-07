"""Gradio entry point for local use and Hugging Face Spaces."""
from pathlib import Path
import os
import sys
from functools import partial

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
os.environ.setdefault('GRADIO_ANALYTICS_ENABLED', 'False')
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')
managed_cache = Path.home() / '.cache/codex-dev/huggingface'
if managed_cache.is_dir():
    os.environ.setdefault('HF_HOME', str(managed_cache))
cloud_mode = bool(os.environ.get('SPACE_ID')) and os.environ.get('FIXMARGE_CLOUD') == '1'
allow_download = cloud_mode or os.environ.get('FIXMARGE_ALLOW_MODEL_DOWNLOAD') == '1'
if not allow_download:
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')

def require_cloud_dictionary():
    from fixmarge.rag import LexiconRAG
    directory = Path(os.environ.get('FIXMARGE_DATA_DIR', str(ROOT / 'data' / 'processed')))
    try:
        # Parse local inputs before any adapter download or model preload.
        configured = bool(LexiconRAG(data_dir=directory).entries)
    except (OSError, ValueError, TypeError, KeyError):
        configured = False
    if not configured:
        raise RuntimeError('⚠ fiXmArge · Coword · ∅ — FIXMARGE_DATA_DIR: lexicon.jsonl + rules.jsonl')


if cloud_mode:
    require_cloud_dictionary()
    import spaces

import gradio as gr
from fixmarge.demo import DemoService, present_result, target_languages, validate_translation_pair

adapter_path = os.environ.get('FIXMARGE_ADAPTER_PATH')
service_options = {}
if cloud_mode:
    from fixmarge.cloud import prepare_cloud_adapter
    from fixmarge.infer import ModelRunner
    adapter_path = str(prepare_cloud_adapter())
    service_options['runner_factory'] = partial(ModelRunner, device_map='cuda')

service = DemoService(data_dir=os.environ.get('FIXMARGE_DATA_DIR'),
    external_dir=os.environ.get('FIXMARGE_EXTERNAL_DIR'),
    model_name=os.environ.get('FIXMARGE_MODEL', 'Qwen/Qwen3-4B-Instruct-2507'),
    adapter=adapter_path,
    device='cuda' if cloud_mode else os.environ.get('FIXMARGE_DEVICE', 'auto'), allow_download=allow_download,
    load_in_4bit=False if cloud_mode else os.environ.get('FIXMARGE_LOAD_IN_4BIT') == '1',
    **service_options)
if cloud_mode:
    service.preload()


def _respond_inference(text, source, target, mode):
    result = service.run(text, source, target, mode == 'generate')
    view = list(present_result(result))
    diagnostic = result.get('diagnostic')
    if diagnostic and diagnostic['schema_valid'] and diagnostic['tentative_translation'] is None:
        view[0] = 'MeMe · ∅ · ⚠'
    return tuple(view)


if cloud_mode:
    _respond_inference = spaces.GPU(duration=60)(_respond_inference)


def respond(text, source, target, mode="generate"):
    try:
        # Validate before ZeroGPU allocation as well as inside DemoService.run.
        validate_translation_pair(source, target)
        return _respond_inference(text, source, target, mode)
    except (ValueError, OSError, RuntimeError) as error:
        raise gr.Error(str(error)) from error


LANGUAGES = [('fiXmArge', 'fix'), ('ko', 'ko'), ('ja', 'ja'), ('en', 'en')]

# Flat dotted keys use Gradio's supported I18n configuration. They are resolved
# before nested vendor defaults, including for browsers using another locale.
UI_MESSAGES = {
    'common.built_with': '⚙', 'common.built_with_gradio': '⚙ Gradio',
    'common.clear': '∅', 'common.download': '↓', 'common.edit': '✎',
    'common.empty': '∅', 'common.error': '⚠', 'common.hosted_on': '☁',
    'common.loading': '⋯', 'common.logo': 'fiXmArge', 'common.or': '/',
    'common.remove': '−', 'common.settings': '⚙', 'common.share': '↗',
    'common.submit': 'ConWas', 'common.undo': '↶', 'common.no_devices': '⚠ ∅',
    'common.language': 'Coword', 'common.display_theme': '◐', 'common.pwa': 'PWA',
    'common.record': '●', 'common.stop_recording': '■', 'common.run': 'ConWas',
    'common.screen_studio': '▣', 'common.share_gradio_tab': '↗ Gradio',
    'blocks.connection_can_break': '⚠ connection_can_break · mobile / sleep',
    'blocks.long_requests_queue': '⚠ queue_waiting',
    'blocks.lost_connection': '⚠ connection_lost · ↶',
    'blocks.waiting_for_inputs': 'Coword · ⋯',
    'errors.build_error': '⚠ build_error', 'errors.config_error': '⚠ config_error',
    'errors.contact_page_author': '⚠ · ↗', 'errors.no_app_file': '⚠ app.py · ∅',
    'errors.runtime_error': '⚠ runtime_error',
    'errors.space_not_working': '⚠ Space · {0}', 'errors.space_paused': 'Space · Ⅱ',
    'errors.use_via_api': 'API', 'errors.use_via_api_or_mcp': 'API / MCP',
    'dataframe.incorrect_format': '⚠ CSV / TSV',
    'dataframe.new_column': '+ │', 'dataframe.new_row': '+ ─',
    'dataframe.add_row_above': '+ ─ ↑', 'dataframe.add_row_below': '+ ─ ↓',
    'dataframe.delete_row': '− ─', 'dataframe.delete_column': '− │',
    'dataframe.add_column_left': '+ │ ←', 'dataframe.add_column_right': '+ │ →',
    'dataframe.sort_column': '│ ↕', 'dataframe.sort_ascending': '↑',
    'dataframe.sort_descending': '↓', 'dataframe.drop_to_upload': '↓ CSV / TSV',
    'dataframe.clear_sort': '↕ ∅', 'dataframe.filter': '⏷',
    'dataframe.clear_filter': '⏷ ∅', 'dropdown.dropdown': '↓',
    'highlighted_text.highlighted_text': 'Coword · ↔',
    'file.uploading': '↑ ⋯',
}
UI_I18N = gr.I18n(**{locale: UI_MESSAGES for locale in (
    'ar', 'ca', 'ckb', 'de', 'en', 'es', 'eu', 'fa', 'fi', 'fr', 'he', 'hi',
    'ja', 'ko', 'lt', 'nb', 'nl', 'pl', 'pt-BR', 'pt', 'ro', 'ru', 'sv',
    'ta', 'th', 'tr', 'uk', 'ur', 'uz', 'zh-CN', 'zh-TW',
)})


def update_target_languages(source, current_target):
    allowed = target_languages(source)
    selected = current_target if current_target in allowed else allowed[0]
    return gr.update(choices=[choice for choice in LANGUAGES if choice[1] in allowed], value=selected)


def build_demo():
    title = 'fiXmArge · ConWas'
    with gr.Blocks(title=title, analytics_enabled=False,
                   css='''
                       #fixmarge-detail .icon-button-wrapper { display: none; }
                       :is(#fixmarge-proposal, #fixmarge-highlights, #fixmarge-evidence,
                           #fixmarge-status, #fixmarge-detail) :is(.progress-text, .loading) {
                           display: none;
                       }
                   ''',
                   theme=gr.themes.Soft(primary_hue='teal', neutral_hue='slate')) as demo:
        gr.Markdown('# ' + title)
        with gr.Row(equal_height=True):
            with gr.Column():
                source = gr.Dropdown(LANGUAGES, value='fix', label='Coword →')
                text = gr.Textbox(label='Coword', placeholder='Coword…', lines=8, max_lines=12)
            with gr.Column():
                target = gr.Dropdown([choice for choice in LANGUAGES if choice[1] in target_languages('fix')],
                                     value='ko', label='→ MeMe')
                proposal = gr.Textbox(label='MeMe', placeholder='MeMe…',
                                      lines=8, max_lines=12, interactive=False, show_copy_button=False,
                                      elem_id='fixmarge-proposal')
        run = gr.Button('ConWas', variant='primary')
        with gr.Accordion('Coword · MeMe · ⚠', open=False):
            highlights = gr.HighlightedText(label='Coword · ↔', elem_id='fixmarge-highlights',
                color_map={'Coword ↔ MeMe':'#a7e3c0','Coword · ?':'#f4b9b5','MeMe · ∅':'#f6df91',
                           'MeMe · ≠':'#f6c39a','MeMe · 1…n':'#d3c5ef','fiXmArge · ∅':'#dde3e9'})
            evidence = gr.Dataframe(headers=['Coword','MeMe','⚑','↗'], datatype=['str']*4,
                                   label='Coword ↔ MeMe', interactive=False, wrap=True, elem_id='fixmarge-evidence')
            status = gr.Textbox(label='⚙ · ⚠', lines=6, interactive=False, elem_id='fixmarge-status')
            with gr.Accordion('{} · ⚙', open=False):
                detail = gr.JSON(label='{}', elem_id='fixmarge-detail')
            examples = [['sinruits', 'fix', 'ko'], ['sinruits', 'fix', 'ja'],
                        ['sinruits', 'fix', 'en']]
            gr.Examples(examples=examples, inputs=[text, source, target], label='Coword')
        source.change(update_target_languages, inputs=[source, target], outputs=target,
                      api_name=False, queue=False, preprocess=False)
        outputs = [proposal, highlights, evidence, status, detail]
        run.click(respond, inputs=[text, source, target], outputs=outputs,
                  api_name='translate', concurrency_limit=1, preprocess=False)
        text.submit(respond, inputs=[text, source, target], outputs=outputs,
                    api_name=False, concurrency_limit=1, preprocess=False)
    return demo.queue(default_concurrency_limit=1, max_size=8)


demo = build_demo()
if __name__ == '__main__':
    demo.launch(server_name='0.0.0.0' if os.environ.get('SPACE_ID') else '127.0.0.1',
                server_port=int(os.environ.get('PORT', '7860')), share=False, i18n=UI_I18N)
